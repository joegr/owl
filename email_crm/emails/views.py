from django.shortcuts import render
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
            subject = template.subject
            body = template.body
        
        # Basic template variable replacement
        body = body.replace('{{name}}', contact.name)
        body = body.replace('{{email}}', contact.email)
        if contact.company:
            body = body.replace('{{company}}', contact.company)
        if contact.position:
            body = body.replace('{{position}}', contact.position)
        
        # Send the email (in production, you'd want to use a background task for this)
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
                fail_silently=False,
            )
            
            # Record the sent email
            sent_email = SentEmail.objects.create(
                user=request.user,
                contact=contact,
                template=template,
                subject=subject,
                body=body
            )
            
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
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        contact_ids = request.data.get('contact_ids', [])
        template_id = request.data.get('template_id')
        
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
        errors = []
        
        for contact in contacts:
            # Basic template variable replacement
            subject = template.subject
            body = template.body.replace('{{name}}', contact.name).replace('{{email}}', contact.email)
            
            if contact.company:
                body = body.replace('{{company}}', contact.company)
            if contact.position:
                body = body.replace('{{position}}', contact.position)
            
            try:
                # Send the email
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[contact.email],
                    fail_silently=False,
                )
                
                # Record the sent email
                sent_email = SentEmail.objects.create(
                    user=request.user,
                    contact=contact,
                    template=template,
                    subject=subject,
                    body=body
                )
                
                # Record activity
                Activity.objects.create(
                    user=request.user,
                    activity_type='email_sent',
                    description=f'Sent email to {contact.name}: {subject}',
                    content_object=sent_email
                )
                
                sent_count += 1
                
            except Exception as e:
                errors.append({
                    'contact_id': contact.id,
                    'contact_name': contact.name,
                    'error': str(e)
                })
        
        return Response({
            'status': 'success',
            'message': f'Successfully sent {sent_count} emails',
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
