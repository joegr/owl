from django.shortcuts import render, redirect
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import EmailTemplate, SentEmail
from .serializers import EmailTemplateSerializer, SentEmailSerializer
from contacts.models import Contact
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from dashboard.models import Activity
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import logging
import csv
import json
import uuid
from django.http import HttpResponse, JsonResponse
from .utils import EmailTemplateProcessor
from campaigns.models import Campaign, CampaignContact
from campaigns.forms import BulkEmailForm
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailTemplateListCreateView(generics.ListCreateAPIView):
    """
    API view to list all email templates and create new ones.
    
    GET: List all email templates belonging to the current user
    POST: Create a new email template
    """
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only templates belonging to the current user."""
        return EmailTemplate.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to the current authenticated user when creating a template."""
        template = serializer.save(user=self.request.user)
        
        # Record activity
        Activity.objects.create(
            user=self.request.user,
            activity_type='template_created',
            description=f'Created email template: {template.name}',
            content_object=template
        )

class EmailTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a specific email template.
    
    GET: Retrieve a template
    PUT/PATCH: Update a template
    DELETE: Delete a template
    """
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only templates belonging to the current user."""
        return EmailTemplate.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        """Record activity when updating a template."""
        template = serializer.save()
        
        # Record activity
        Activity.objects.create(
            user=self.request.user,
            activity_type='template_updated',
            description=f'Updated email template: {template.name}',
            content_object=template
        )
    
    def perform_destroy(self, instance):
        """Record activity when deleting a template."""
        template_name = instance.name
        
        # Delete the template
        instance.delete()
        
        # Record activity
        Activity.objects.create(
            user=self.request.user,
            activity_type='template_deleted',
            description=f'Deleted email template: {template_name}'
        )

class SendEmailView(APIView):
    """
    API view to send an email to a contact.
    
    POST: Send an email to a contact
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, contact_id):
        # Get the contact and check if it belongs to the user
        contact = get_object_or_404(Contact, id=contact_id, user=request.user)
        
        # Get the template if provided
        template_id = request.data.get('template_id')
        template = None
        subject = request.data.get('subject', '')
        body = request.data.get('body', '')
        
        if template_id:
            template = get_object_or_404(EmailTemplate, id=template_id, user=request.user)
            # Use template for subject/body if not explicitly provided
            if not subject:
                subject = template.subject
            if not body:
                body = template.body
        
        # Use the template processor to replace variables
        subject = EmailTemplateProcessor.process_template(subject, contact)
        body = EmailTemplateProcessor.process_template(body, contact)
        
        # Send the email (in production, you'd want to use a background task for this)
        try:
            # Create a tracking ID for this email
            tracking_id = str(uuid.uuid4())
            
            # Record the sent email before sending
            sent_email = SentEmail.objects.create(
                user=request.user,
                contact=contact,
                template=template,
                subject=subject,
                body=body,
                tracking_id=tracking_id,
                status='pending'
            )
            
            # Send email with Django's EmailMessage
            from django.core.mail import EmailMessage
            message = EmailMessage(
                subject=subject,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contact.email],
            )
            
            # Set the body
            message.body = body
            
            # Prepare message headers for tracking
            message.extra_headers = {
                'X-Mailgun-Track': 'yes',
                'X-Mailgun-Track-Clicks': 'yes',
                'X-Mailgun-Track-Opens': 'yes',
                'X-Mailgun-Variables': json.dumps({'tracking_id': tracking_id}),
            }
            
            # Send the message
            message_id = message.send()
            
            # Update the sent email with the Mailgun ID
            sent_email.mailgun_id = message_id
            sent_email.status = 'sent'
            sent_email.save()
            
            # Record activity
            Activity.objects.create(
                user=request.user,
                activity_type='email_sent',
                description=f'Sent email to {contact.name}: {subject}',
                content_object=sent_email
            )
            
            return Response({
                'status': 'success',
                'message': 'Email sent successfully',
                'email': SentEmailSerializer(sent_email).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BulkSendEmailView(APIView):
    """
    API view to send emails to multiple contacts.
    
    POST: Send emails to multiple contacts
    POST with scheduled_time: Schedule emails for future delivery
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        contact_ids = request.data.get('contact_ids', [])
        template_id = request.data.get('template_id')
        scheduled_time = request.data.get('scheduled_time')
        
        if not contact_ids or not template_id:
            return Response({
                'status': 'error',
                'message': 'Both contact_ids and template_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the template
        template = get_object_or_404(EmailTemplate, id=template_id, user=request.user)
        
        # Get contacts that belong to the user
        contacts = Contact.objects.filter(
            id__in=contact_ids, 
            user=request.user
        )
        
        sent_count = 0
        scheduled_count = 0
        errors = []
        
        # Check if this is a scheduled email
        is_scheduled = scheduled_time is not None
        
        for contact in contacts:
            # Basic template variable replacement
            subject = template.subject
            body = template.body
            
            # Use the template processor to replace variables
            subject = EmailTemplateProcessor.process_template(subject, contact)
            body = EmailTemplateProcessor.process_template(body, contact)
            
            try:
                # Record the email
                sent_email = SentEmail.objects.create(
                    user=request.user,
                    contact=contact,
                    template=template,
                    subject=subject,
                    body=body,
                    # Store the scheduled time if provided
                    scheduled_time=scheduled_time if is_scheduled else None
                )
                
                # Only send immediately if not scheduled for future
                if not is_scheduled:
                    # Create a tracking ID for this email
                    tracking_id = str(uuid.uuid4())
                    
                    # Update the sent email with tracking info
                    sent_email.tracking_id = tracking_id
                    sent_email.status = 'pending'
                    sent_email.save()
                    
                    # Send email with Django's EmailMessage
                    from django.core.mail import EmailMessage
                    message = EmailMessage(
                        subject=subject,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[contact.email],
                    )
                    
                    # Set the body
                    message.body = body
                    
                    # Prepare message headers for tracking
                    message.extra_headers = {
                        'X-Mailgun-Track': 'yes',
                        'X-Mailgun-Track-Clicks': 'yes',
                        'X-Mailgun-Track-Opens': 'yes',
                        'X-Mailgun-Variables': json.dumps({'tracking_id': tracking_id}),
                    }
                    
                    # Send the message
                    message_id = message.send()
                    
                    # Update the sent email with the Mailgun ID
                    sent_email.mailgun_id = message_id
                    sent_email.status = 'sent'
                    sent_email.save()
                    
                    # Record activity for immediate sending
                    Activity.objects.create(
                        user=request.user,
                        activity_type='email_sent',
                        description=f'Sent email to {contact.name}: {subject}',
                        content_object=sent_email
                    )
                    
                    sent_count += 1
                else:
                    # Record activity for scheduling
                    Activity.objects.create(
                        user=request.user,
                        activity_type='email_scheduled',
                        description=f'Scheduled email to {contact.name} for {scheduled_time}',
                        content_object=sent_email
                    )
                    
                    scheduled_count += 1
                
            except Exception as e:
                errors.append({
                    'contact_id': contact.id,
                    'contact_name': contact.name,
                    'error': str(e)
                })
        
        # Prepare appropriate response message
        if is_scheduled:
            message = f'Successfully scheduled {scheduled_count} emails for {scheduled_time}'
        else:
            message = f'Successfully sent {sent_count} emails'
            
        return Response({
            'status': 'success',
            'message': message,
            'errors': errors
        }, status=status.HTTP_200_OK)

class EmailAnalyticsView(APIView):
    """
    API view to get analytics on sent emails.
    
    GET: Get email analytics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get basic analytics on sent emails
        total_sent = SentEmail.objects.filter(user=request.user).count()
        total_opened = SentEmail.objects.filter(user=request.user, opened=True).count()
        total_clicked = SentEmail.objects.filter(user=request.user, clicked=True).count()
        
        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        
        # Get emails sent per template
        template_stats = SentEmail.objects.filter(user=request.user, template__isnull=False) \
            .values('template__name') \
            .annotate(
                sent_count=Count('id'),
                opened_count=Count('id', filter=Q(opened=True)),
                clicked_count=Count('id', filter=Q(clicked=True))
            )
        
        # Get recent sent emails
        recent_emails = SentEmail.objects.filter(user=request.user).order_by('-sent_at')[:10]
        
        return Response({
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
            'template_stats': template_stats,
            'recent_emails': SentEmailSerializer(recent_emails, many=True).data
        }, status=status.HTTP_200_OK)

class ExportAnalyticsView(APIView):
    """
    API view to export email analytics data.
    
    GET: Export analytics data in the specified format
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        format_type = request.query_params.get('format', 'csv')
        
        # Get the data to export
        emails = SentEmail.objects.filter(user=request.user).order_by('-sent_at')
        
        if format_type == 'csv':
            # Create a CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="email_analytics.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Contact', 'Email', 'Subject', 'Sent At', 
                'Status', 'Opened', 'Opened At', 'Open Count',
                'Clicked', 'Clicked At', 'Click Count'
            ])
            
            for email in emails:
                writer.writerow([
                    email.id,
                    email.contact.name,
                    email.contact.email,
                    email.subject,
                    email.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
                    email.status,
                    'Yes' if email.opened else 'No',
                    email.opened_at.strftime('%Y-%m-%d %H:%M:%S') if email.opened_at else '',
                    email.open_count,
                    'Yes' if email.clicked else 'No',
                    email.clicked_at.strftime('%Y-%m-%d %H:%M:%S') if email.clicked_at else '',
                    email.click_count
                ])
            
            return response
        
        elif format_type == 'json':
            # Create a JSON response
            data = []
            
            for email in emails:
                data.append({
                    'id': email.id,
                    'contact': {
                        'id': email.contact.id,
                        'name': email.contact.name,
                        'email': email.contact.email
                    },
                    'subject': email.subject,
                    'sent_at': email.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': email.status,
                    'opened': email.opened,
                    'opened_at': email.opened_at.strftime('%Y-%m-%d %H:%M:%S') if email.opened_at else None,
                    'open_count': email.open_count,
                    'clicked': email.clicked,
                    'clicked_at': email.clicked_at.strftime('%Y-%m-%d %H:%M:%S') if email.clicked_at else None,
                    'click_count': email.click_count
                })
            
            return JsonResponse(data, safe=False)
        
        else:
            return Response({
                'status': 'error',
                'message': f'Unsupported export format: {format_type}'
            }, status=status.HTTP_400_BAD_REQUEST)

# Template-based views for the email sending process
@login_required
def compose_email_view(request, contact_id):
    """
    View to display the email composition form.
    
    GET: Show the form to compose an email to a contact
    """
    # Get the contact and check if it belongs to the user
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    # Get available templates for this user
    templates = EmailTemplate.objects.filter(user=request.user)
    
    return render(request, 'emails/email_form.html', {
        'contact': contact,
        'templates': templates
    })

@login_required
def preview_email_view(request, contact_id):
    """
    View to preview the email before sending.
    
    POST: Process the email form data and show a preview
    """
    if request.method != 'POST':
        return redirect('emails:compose_email', contact_id=contact_id)
    
    # Get the contact and check if it belongs to the user
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    # Process form data
    subject = request.POST.get('subject', '')
    body = request.POST.get('body', '')
    template_id = request.POST.get('template_id', '')
    
    # Use the template processor to replace variables
    subject = EmailTemplateProcessor.process_template(subject, contact)
    body = EmailTemplateProcessor.process_template(body, contact)
    
    # Store the data for preview
    email_data = {
        'subject': subject,
        'body': body,
    }
    
    if template_id:
        email_data['template_id'] = template_id
    
    return render(request, 'emails/email_preview.html', {
        'contact': contact,
        'email_data': email_data
    })

@login_required
def send_email_view(request, contact_id):
    """
    View to actually send the email after preview confirmation.
    
    POST: Send the email to the contact
    """
    if request.method != 'POST':
        return redirect('emails:compose_email', contact_id=contact_id)
    
    # Get the contact and check if it belongs to the user
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    # Get the email data from the form
    subject = request.POST.get('subject', '')
    body = request.POST.get('body', '')
    template_id = request.POST.get('template_id', '')
    
    # Get the template if provided
    template = None
    if template_id:
        template = get_object_or_404(EmailTemplate, id=template_id, user=request.user)
    
    # Use the template processor to replace variables
    subject = EmailTemplateProcessor.process_template(subject, contact)
    body = EmailTemplateProcessor.process_template(body, contact)
    
    # Send the email
    try:
        # Create a tracking ID for this email
        tracking_id = str(uuid.uuid4())
        
        # Record the sent email before sending
        sent_email = SentEmail.objects.create(
            user=request.user,
            contact=contact,
            template=template,
            subject=subject,
            body=body,
            tracking_id=tracking_id,
            status='pending'
        )
        
        # Send email with Django's EmailMessage
        from django.core.mail import EmailMessage
        message = EmailMessage(
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact.email],
        )
        
        # Set the body
        message.body = body
        
        # Prepare message headers for tracking
        message.extra_headers = {
            'X-Mailgun-Track': 'yes',
            'X-Mailgun-Track-Clicks': 'yes',
            'X-Mailgun-Track-Opens': 'yes',
            'X-Mailgun-Variables': json.dumps({'tracking_id': tracking_id}),
        }
        
        # Send the message
        message_id = message.send()
        
        # Update the sent email with the Mailgun ID
        sent_email.mailgun_id = message_id
        sent_email.status = 'sent'
        sent_email.save()
        
        # Record activity
        Activity.objects.create(
            user=request.user,
            activity_type='email_sent',
            description=f'Sent email to {contact.name}: {subject}',
            content_object=sent_email
        )
        
        # Add success message
        messages.success(request, f'Email successfully sent to {contact.name}!')
        
        # Redirect to the contact detail page
        return redirect('contacts:view', contact.id)
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('emails:compose_email', contact_id=contact_id)

@login_required
def select_contact_view(request):
    """View to select a contact before composing an email."""
    contacts = Contact.objects.filter(user=request.user).order_by('name')
    return render(request, 'emails/select_contact_for_email.html', {'contacts': contacts})

@login_required
def email_analytics_dashboard_view(request):
    """View to display the visual email analytics dashboard."""
    return render(request, 'emails/analytics_dashboard.html')

@login_required
def bulk_compose_email_view(request):
    """View for composing bulk emails to multiple contacts."""
    # Get contact IDs from POST or GET
    contact_ids_str = request.POST.get('contact_ids', '')
    
    # If not in POST, check for GET parameter
    if not contact_ids_str and 'contact_ids' in request.GET:
        contact_ids_str = request.GET.get('contact_ids', '')
    
    # Process contact IDs from POST or GET parameters
    if contact_ids_str:
        try:
            contact_ids = [int(id.strip()) for id in contact_ids_str.split(',') if id.strip()]
            # Store contact IDs in session for persistence between requests
            request.session['bulk_contacts'] = contact_ids
        except ValueError:
            contact_ids = []
    else:
        # Try to get from session
        contact_ids = request.session.get('bulk_contacts', [])
    
    # Get contacts belonging to the user
    contacts = Contact.objects.filter(user=request.user, id__in=contact_ids)
    contact_count = contacts.count()
    
    if request.method == 'POST' and 'subject' in request.POST:
        form = BulkEmailForm(request.user, request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            email_template = form.cleaned_data.get('email_template')
            save_as_template = form.cleaned_data.get('save_as_template')
            template_name = form.cleaned_data.get('template_name')
            create_campaign = form.cleaned_data.get('create_campaign')
            campaign_name = form.cleaned_data.get('campaign_name')
            
            # Save as a new template if requested
            if save_as_template and template_name:
                new_template = EmailTemplate.objects.create(
                    user=request.user,
                    name=template_name,
                    subject=subject,
                    body=body
                )
                # Record activity
                Activity.objects.create(
                    user=request.user,
                    activity_type='template_created',
                    description=f'Created email template: {new_template.name}',
                    content_object=new_template
                )
            
            # Create a campaign if requested
            campaign = None
            if create_campaign and campaign_name:
                campaign = Campaign.objects.create(
                    user=request.user,
                    name=campaign_name,
                    description=f"Bulk email sent on {datetime.now().strftime('%Y-%m-%d')}",
                    email_template=email_template
                )
                
                # Add contacts to campaign
                for contact in contacts:
                    CampaignContact.objects.create(
                        campaign=campaign,
                        contact=contact
                    )
            
            # Store data in session for confirmation page
            request.session['bulk_email_data'] = {
                'subject': subject,
                'body': body,
                'contact_ids': [str(contact.id) for contact in contacts],
                'template_id': email_template.id if email_template else None,
                'campaign_id': campaign.id if campaign else None
            }
            
            # Save session to ensure data is persisted
            request.session.modified = True
            
            return redirect('emails:bulk_send_email')
    else:
        form = BulkEmailForm(request.user)
    
    return render(request, 'emails/bulk_email/compose.html', {
        'form': form,
        'contacts': contacts,
        'contact_count': contact_count,
        'contact_ids': ','.join([str(contact.id) for contact in contacts])
    })

@login_required
def bulk_send_email_view(request):
    """View for sending bulk emails to multiple contacts."""
    # Get data from session
    bulk_email_data = request.session.get('bulk_email_data', {})
    
    # Check if we're coming directly from a campaign
    campaign_id = request.GET.get('campaign_id')
    if campaign_id and not bulk_email_data:
        try:
            campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
            
            # Get all contacts for this campaign
            campaign_contacts = CampaignContact.objects.filter(campaign=campaign)
            contacts = [cc.contact for cc in campaign_contacts]
            contact_ids = [str(contact.id) for contact in contacts]
            
            # Create bulk email data
            bulk_email_data = {
                'subject': campaign.subject,
                'body': campaign.content,
                'contact_ids': contact_ids,
                'template_id': campaign.email_template.id if campaign.email_template else None,
                'campaign_id': campaign.id
            }
            
            # Store in session
            request.session['bulk_email_data'] = bulk_email_data
            request.session.modified = True
        except Exception as e:
            logger.error(f"Error preparing campaign {campaign_id} for bulk send: {str(e)}")
            messages.error(request, "Error preparing campaign for sending. Please try again.")
            return redirect('campaigns:detail', campaign_id=campaign_id)
    
    if not bulk_email_data:
        messages.error(request, "Email data not found. Please try again.")
        return redirect('contacts:list')
    
    # Make a copy to avoid modifying the session data directly
    email_data = bulk_email_data.copy()
    
    subject = email_data.get('subject')
    body = email_data.get('body')
    contact_ids = email_data.get('contact_ids', [])
    template_id = email_data.get('template_id')
    campaign_id = email_data.get('campaign_id')
    
    # Get related objects
    contacts = Contact.objects.filter(user=request.user, id__in=contact_ids)
    template = None
    if template_id:
        template = get_object_or_404(EmailTemplate, id=template_id, user=request.user)
    
    campaign = None
    if campaign_id:
        campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if request.method == 'POST':
        emails_sent = 0
        emails_failed = 0
        
        for contact in contacts:
            # Process template with contact data
            processed_subject = EmailTemplateProcessor.process_template(subject, contact)
            processed_body = EmailTemplateProcessor.process_template(body, contact)
            
            # Generate tracking ID
            tracking_id = str(uuid.uuid4())
            
            try:
                # Create sent email record
                sent_email = SentEmail.objects.create(
                    user=request.user,
                    contact=contact,
                    template=template,
                    subject=processed_subject,
                    body=processed_body,
                    tracking_id=tracking_id,
                    status='pending'
                )
                
                # Create email message
                from django.core.mail import EmailMessage
                message = EmailMessage(
                    subject=processed_subject,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[contact.email],
                )
                
                # Set body
                message.body = processed_body
                
                # Set headers for tracking
                message.extra_headers = {
                    'X-Mailgun-Track': 'yes',
                    'X-Mailgun-Track-Clicks': 'yes',
                    'X-Mailgun-Track-Opens': 'yes',
                    'X-Mailgun-Variables': json.dumps({'tracking_id': tracking_id}),
                }
                
                # Send email
                message_id = message.send()
                
                # Update sent email record
                sent_email.mailgun_id = message_id
                sent_email.status = 'sent'
                sent_email.save()
                
                # Update campaign contact if this is part of a campaign
                if campaign:
                    campaign_contact = CampaignContact.objects.get(campaign=campaign, contact=contact)
                    campaign_contact.is_sent = True
                    campaign_contact.sent_at = datetime.now()
                    campaign_contact.save()
                
                emails_sent += 1
                
                # Record activity
                Activity.objects.create(
                    user=request.user,
                    activity_type='email_sent',
                    description=f'Sent email to {contact.name}: {processed_subject}',
                    content_object=sent_email
                )
                
            except Exception as e:
                logger.error(f"Failed to send email to {contact.email}: {str(e)}")
                emails_failed += 1
        
        # Update campaign status if all emails are sent
        if campaign and emails_failed == 0:
            campaign.is_sent = True
            campaign.sent_at = datetime.now()
            campaign.save()
        
        # Clear session data
        if 'bulk_email_data' in request.session:
            del request.session['bulk_email_data']
        if 'bulk_contacts' in request.session:
            del request.session['bulk_contacts']
        
        # Save session changes
        request.session.modified = True
        
        # Show success/error message
        if emails_failed == 0:
            messages.success(request, f"Successfully sent {emails_sent} emails.")
        else:
            messages.warning(request, f"Sent {emails_sent} emails, but {emails_failed} failed to send.")
        
        # Redirect based on where we came from
        if campaign:
            return redirect('campaigns:detail', campaign_id=campaign.id)
        else:
            return redirect('contacts:list')
    
    return render(request, 'emails/bulk_email/confirm.html', {
        'subject': subject,
        'body': body,
        'contacts': contacts,
        'contact_count': contacts.count(),
        'template': template,
        'campaign': campaign
    })
