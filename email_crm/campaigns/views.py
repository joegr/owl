from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import Campaign, CampaignContact, CampaignList
from .forms import CampaignForm, CampaignListForm
from contacts.models import Contact
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from emails.models import EmailTemplate

@login_required
def campaign_list(request):
    """View to list all campaigns."""
    campaigns = Campaign.objects.filter(user=request.user).annotate(
        contact_count=Count('campaign_contacts'),
        opened_count=Count('campaign_contacts', filter=Q(campaign_contacts__opened=True)),
        clicked_count=Count('campaign_contacts', filter=Q(campaign_contacts__clicked=True))
    )
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status == 'sent':
        campaigns = campaigns.filter(is_sent=True)
    elif status == 'pending':
        campaigns = campaigns.filter(is_sent=False)
    
    # Search if specified
    search = request.GET.get('search')
    if search:
        campaigns = campaigns.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    return render(request, 'campaigns/campaign_list.html', {
        'campaigns': campaigns
    })

@login_required
def campaign_detail(request, campaign_id):
    """View to show campaign details and analytics."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    # Get campaign contacts with tracking statistics
    campaign_contacts = CampaignContact.objects.filter(campaign=campaign)
    
    # Calculate statistics
    total_contacts = campaign_contacts.count()
    sent_count = campaign_contacts.filter(is_sent=True).count()
    opened_count = campaign_contacts.filter(opened=True).count()
    clicked_count = campaign_contacts.filter(clicked=True).count()
    
    # Calculate rates
    open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
    click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
    
    return render(request, 'campaigns/campaign_detail.html', {
        'campaign': campaign,
        'campaign_contacts': campaign_contacts,
        'total_contacts': total_contacts,
        'sent_count': sent_count,
        'opened_count': opened_count,
        'clicked_count': clicked_count,
        'open_rate': open_rate,
        'click_rate': click_rate
    })

@login_required
def campaign_create(request):
    """View to create a new campaign."""
    # Initialize selected_contact_ids
    selected_contact_ids = []
    
    if request.method == 'POST':
        form = CampaignForm(request.user, request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user
            campaign.save()
            
            # Handle contact selection based on method
            recipient_type = request.POST.get('recipient_type', 'list')
            
            if recipient_type == 'list':
                # Get contacts from the selected list
                contact_list = form.cleaned_data.get('contact_list')
                if contact_list:
                    contacts = contact_list.contacts.all()
                    
                    # Add contacts to the campaign
                    for contact in contacts:
                        CampaignContact.objects.create(
                            campaign=campaign,
                            contact=contact
                        )
            else:
                # Get contacts based on filters
                companies = form.cleaned_data.get('companies', [])
                positions = form.cleaned_data.get('positions', [])
                
                contacts_query = Contact.objects.filter(user=request.user)
                
                if companies:
                    contacts_query = contacts_query.filter(company__in=companies)
                if positions:
                    contacts_query = contacts_query.filter(position__in=positions)
                
                # Add contacts to the campaign
                for contact in contacts_query:
                    CampaignContact.objects.create(
                        campaign=campaign,
                        contact=contact
                    )
            
            # Clear any session data
            if 'campaign_form_data' in request.session:
                del request.session['campaign_form_data']
                request.session.modified = True
            
            messages.success(request, f"Campaign '{campaign.name}' created successfully.")
            return redirect('campaigns:detail', campaign_id=campaign.id)
        else:
            # If form is invalid, store the valid fields in session
            session_data = {}
            for key, value in form.cleaned_data.items():
                if key in form.cleaned_data and not isinstance(value, (list, dict, CampaignList)):
                    try:
                        # Ensure the value is JSON serializable
                        session_data[key] = str(value) if value is not None else None
                    except:
                        pass
            
            # Store recipient type in session
            session_data['recipient_type'] = request.POST.get('recipient_type', 'list')
            
            # For filter-based selection, store filter values
            if session_data['recipient_type'] == 'filter':
                # These can be stored as lists since they're just strings
                if 'companies' in form.cleaned_data:
                    session_data['companies'] = list(form.cleaned_data['companies'])
                if 'positions' in form.cleaned_data:
                    session_data['positions'] = list(form.cleaned_data['positions'])
                
            # For list-based selection, store list ID if available
            elif 'contact_list' in form.cleaned_data and form.cleaned_data['contact_list']:
                session_data['contact_list_id'] = str(form.cleaned_data['contact_list'].id)
            
            request.session['campaign_form_data'] = session_data
            request.session.modified = True
    else:
        # Try to get data from session or initialize new form
        initial_data = {}
        
        if 'campaign_form_data' in request.session:
            session_data = request.session.get('campaign_form_data', {})
            
            # Process the data from session
            for key, value in session_data.items():
                if key != 'contact_list_id' and key != 'recipient_type' and key != 'companies' and key != 'positions':
                    initial_data[key] = value
            
            # Handle contact list if stored
            if 'contact_list_id' in session_data:
                try:
                    contact_list = CampaignList.objects.get(id=session_data['contact_list_id'], user=request.user)
                    initial_data['contact_list'] = contact_list
                except (CampaignList.DoesNotExist, ValueError):
                    pass
                    
            form = CampaignForm(request.user, initial=initial_data)
            
            # If navigating from bulk compose, try to get contact IDs from session
            if 'bulk_contacts' in request.session:
                selected_contact_ids = request.session.get('bulk_contacts', [])
        else:
            form = CampaignForm(request.user)
    
    # Get all contacts for the user
    contacts = Contact.objects.filter(user=request.user)
    
    # Get all contact lists for the user
    contact_lists = CampaignList.objects.filter(user=request.user)
    
    # Get query parameter for pre-selecting a list
    list_id = request.GET.get('list_id')
    if list_id:
        try:
            # Verify the list exists and belongs to the user
            contact_list = CampaignList.objects.get(id=list_id, user=request.user)
            form.initial['contact_list'] = contact_list
        except CampaignList.DoesNotExist:
            pass
    
    # Get the saved recipient type from session
    recipient_type = 'list'
    if 'campaign_form_data' in request.session:
        session_data = request.session.get('campaign_form_data', {})
        recipient_type = session_data.get('recipient_type', 'list')
        
        # Restore filter values if using filter method
        companies = session_data.get('companies', [])
        positions = session_data.get('positions', [])
    else:
        companies = []
        positions = []
    
    return render(request, 'campaigns/campaign_form.html', {
        'form': form,
        'contacts': contacts,
        'contact_lists': contact_lists,
        'selected_contact_ids': selected_contact_ids,
        'action': 'Create',
        'recipient_type': recipient_type,
        'selected_companies': companies,
        'selected_positions': positions,
    })

@login_required
def campaign_edit(request, campaign_id):
    """View to edit an existing campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    # Get existing campaign contacts
    campaign_contacts = CampaignContact.objects.filter(campaign=campaign)
    
    if request.method == 'POST':
        form = CampaignForm(request.user, request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            
            # Handle contact selection based on method
            recipient_type = request.POST.get('recipient_type', 'list')
            
            # First, remove all existing contacts
            CampaignContact.objects.filter(campaign=campaign).delete()
            
            if recipient_type == 'list':
                # Get contacts from the selected list
                contact_list = form.cleaned_data.get('contact_list')
                if contact_list:
                    contacts = contact_list.contacts.all()
                    
                    # Add contacts to the campaign
                    for contact in contacts:
                        CampaignContact.objects.create(
                            campaign=campaign,
                            contact=contact
                        )
            else:
                # Get contacts based on filters
                companies = form.cleaned_data.get('companies', [])
                positions = form.cleaned_data.get('positions', [])
                
                contacts_query = Contact.objects.filter(user=request.user)
                
                if companies:
                    contacts_query = contacts_query.filter(company__in=companies)
                if positions:
                    contacts_query = contacts_query.filter(position__in=positions)
                
                # Add contacts to the campaign
                for contact in contacts_query:
                    CampaignContact.objects.create(
                        campaign=campaign,
                        contact=contact
                    )
            
            # Clear any session data
            if 'campaign_form_data' in request.session:
                del request.session['campaign_form_data']
                request.session.modified = True
            
            messages.success(request, f"Campaign '{campaign.name}' updated successfully.")
            return redirect('campaigns:detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(request.user, instance=campaign)
    
    # Determine recipient type and selection based on existing campaign contacts
    recipient_type = 'list'
    selected_companies = []
    selected_positions = []
    contact_list = None
    
    # Get all contact lists for the user
    contact_lists = CampaignList.objects.filter(user=request.user)
    
    # Try to find if these contacts match a list
    if campaign_contacts.exists():
        campaign_contact_ids = set(campaign_contacts.values_list('contact__id', flat=True))
        
        # Check each list to see if it matches the campaign contacts exactly
        for cl in contact_lists:
            list_contact_ids = set(cl.contacts.values_list('id', flat=True))
            if list_contact_ids == campaign_contact_ids:
                contact_list = cl
                form.initial['contact_list'] = cl
                break
        
        # If no matching list found, assume filter-based selection
        if not contact_list:
            recipient_type = 'filter'
            # Get unique companies and positions from the contacts
            contacts = Contact.objects.filter(id__in=campaign_contact_ids)
            selected_companies = list(contacts.values_list('company', flat=True).distinct())
            selected_companies = [c for c in selected_companies if c]
            selected_positions = list(contacts.values_list('position', flat=True).distinct())
            selected_positions = [p for p in selected_positions if p]
            
            # Set initial values for the form
            form.initial['companies'] = selected_companies
            form.initial['positions'] = selected_positions
    
    # Get all contacts for the user
    contacts = Contact.objects.filter(user=request.user)
    
    return render(request, 'campaigns/campaign_form.html', {
        'form': form,
        'campaign': campaign,
        'contacts': contacts,
        'contact_lists': contact_lists,
        'action': 'Edit',
        'recipient_type': recipient_type,
        'selected_companies': selected_companies,
        'selected_positions': selected_positions,
    })

@login_required
def campaign_delete(request, campaign_id):
    """View to delete a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if request.method == 'POST':
        campaign_name = campaign.name
        campaign.delete()
        messages.success(request, f"Campaign '{campaign_name}' deleted successfully.")
        return redirect('campaigns:list')
    
    return render(request, 'campaigns/campaign_confirm_delete.html', {
        'campaign': campaign
    })

@login_required
def list_list(request):
    """View to list all contact lists."""
    contact_lists = CampaignList.objects.filter(user=request.user).annotate(
        contact_count=Count('contacts')
    )
    
    # Search if specified
    search = request.GET.get('search')
    if search:
        contact_lists = contact_lists.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    return render(request, 'campaigns/list_list.html', {
        'contact_lists': contact_lists
    })

@login_required
def list_detail(request, list_id):
    """View to show contact list details."""
    contact_list = get_object_or_404(CampaignList, id=list_id, user=request.user)
    contacts = contact_list.contacts.all()
    
    return render(request, 'campaigns/list_detail.html', {
        'contact_list': contact_list,
        'contacts': contacts
    })

@login_required
def list_create(request):
    """View to create a new contact list."""
    if request.method == 'POST':
        form = CampaignListForm(request.user, request.POST)
        if form.is_valid():
            contact_list = form.save(commit=False)
            contact_list.user = request.user
            contact_list.save()
            
            # Add selected contacts
            form.save_m2m()
            
            messages.success(request, f"Contact list '{contact_list.name}' created successfully.")
            return redirect('campaigns:list_detail', list_id=contact_list.id)
    else:
        form = CampaignListForm(request.user)
    
    return render(request, 'campaigns/list_form.html', {
        'form': form,
        'action': 'Create'
    })

@login_required
def list_edit(request, list_id):
    """View to edit an existing contact list."""
    contact_list = get_object_or_404(CampaignList, id=list_id, user=request.user)
    
    if request.method == 'POST':
        form = CampaignListForm(request.user, request.POST, instance=contact_list)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contact list '{contact_list.name}' updated successfully.")
            return redirect('campaigns:list_detail', list_id=contact_list.id)
    else:
        form = CampaignListForm(request.user, instance=contact_list)
    
    return render(request, 'campaigns/list_form.html', {
        'form': form,
        'contact_list': contact_list,
        'action': 'Edit'
    })

@login_required
def list_delete(request, list_id):
    """View to delete a contact list."""
    contact_list = get_object_or_404(CampaignList, id=list_id, user=request.user)
    
    if request.method == 'POST':
        list_name = contact_list.name
        contact_list.delete()
        messages.success(request, f"Contact list '{list_name}' deleted successfully.")
        return redirect('campaigns:list_list')
    
    return render(request, 'campaigns/list_confirm_delete.html', {
        'contact_list': contact_list
    })

class CampaignListAPIView(APIView):
    """
    API view to list all campaigns and create new ones.
    
    GET: List all campaigns belonging to the current user
    POST: Create a new campaign
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return all campaigns for the current user."""
        campaigns = Campaign.objects.filter(user=request.user).annotate(
            contact_count=Count('campaign_contacts'),
            opened_count=Count('campaign_contacts', filter=Q(campaign_contacts__opened=True)),
            clicked_count=Count('campaign_contacts', filter=Q(campaign_contacts__clicked=True))
        )
        
        campaign_data = []
        for campaign in campaigns:
            # Calculate rates
            sent_count = campaign.campaign_contacts.filter(is_sent=True).count()
            opened_count = campaign.opened_count
            opened_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
            clicked_rate = (campaign.clicked_count / opened_count * 100) if opened_count > 0 else 0
            
            campaign_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'template_name': campaign.email_template.name if campaign.email_template else None,
                'template_id': campaign.email_template.id if campaign.email_template else None,
                'contact_count': campaign.contact_count,
                'sent_count': sent_count,
                'opened_count': opened_count,
                'clicked_count': campaign.clicked_count,
                'open_rate': round(opened_rate, 1),
                'click_rate': round(clicked_rate, 1),
                'created_at': campaign.created_at.isoformat(),
                'updated_at': campaign.updated_at.isoformat(),
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                'is_sent': campaign.is_sent,
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None
            })
        
        return Response(campaign_data)
    
    def post(self, request):
        """Create a new campaign."""
        # Basic validation
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the campaign
        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            description=request.data.get('description', ''),
            scheduled_at=request.data.get('scheduled_at')
        )
        
        # Set email template if provided
        template_id = request.data.get('template_id')
        if template_id:
            try:
                template = EmailTemplate.objects.get(id=template_id, user=request.user)
                campaign.email_template = template
                campaign.save()
            except EmailTemplate.DoesNotExist:
                pass
        
        # Add contacts if provided
        contact_ids = request.data.get('contact_ids', [])
        contacts = Contact.objects.filter(user=request.user, id__in=contact_ids)
        
        for contact in contacts:
            CampaignContact.objects.create(
                campaign=campaign,
                contact=contact
            )
        
        return Response({
            'id': campaign.id,
            'name': campaign.name,
            'success': True,
            'message': f"Campaign '{campaign.name}' created successfully"
        }, status=status.HTTP_201_CREATED)

class CampaignDetailAPIView(APIView):
    """
    API view for a specific campaign.
    
    GET: Get campaign details
    PUT: Update campaign
    DELETE: Delete campaign
    """
    permission_classes = [IsAuthenticated]
    
    def get_campaign(self, campaign_id, user):
        """Helper to get a campaign by ID for the current user."""
        return get_object_or_404(Campaign, id=campaign_id, user=user)
    
    def get(self, request, campaign_id):
        """Get details for a specific campaign."""
        campaign = self.get_campaign(campaign_id, request.user)
        
        # Get campaign contacts
        campaign_contacts = CampaignContact.objects.filter(campaign=campaign)
        
        # Calculate statistics
        total_contacts = campaign_contacts.count()
        sent_count = campaign_contacts.filter(is_sent=True).count()
        opened_count = campaign_contacts.filter(opened=True).count()
        clicked_count = campaign_contacts.filter(clicked=True).count()
        
        # Calculate rates
        open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
        
        # Get contact data
        contacts_data = []
        for cc in campaign_contacts:
            contacts_data.append({
                'id': cc.contact.id,
                'name': cc.contact.name,
                'email': cc.contact.email,
                'is_sent': cc.is_sent,
                'sent_at': cc.sent_at.isoformat() if cc.sent_at else None,
                'opened': cc.opened,
                'opened_at': cc.opened_at.isoformat() if cc.opened_at else None,
                'clicked': cc.clicked,
                'clicked_at': cc.clicked_at.isoformat() if cc.clicked_at else None
            })
        
        return Response({
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'template_name': campaign.email_template.name if campaign.email_template else None,
            'template_id': campaign.email_template.id if campaign.email_template else None,
            'total_contacts': total_contacts,
            'sent_count': sent_count,
            'opened_count': opened_count,
            'clicked_count': clicked_count,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
            'created_at': campaign.created_at.isoformat(),
            'updated_at': campaign.updated_at.isoformat(),
            'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
            'is_sent': campaign.is_sent,
            'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None,
            'contacts': contacts_data
        })
    
    def put(self, request, campaign_id):
        """Update a campaign."""
        campaign = self.get_campaign(campaign_id, request.user)
        
        # Update basic fields
        campaign.name = request.data.get('name', campaign.name)
        campaign.description = request.data.get('description', campaign.description)
        
        # Update scheduled time if provided
        scheduled_at = request.data.get('scheduled_at')
        if scheduled_at is not None:
            campaign.scheduled_at = scheduled_at
        
        # Update template if provided
        template_id = request.data.get('template_id')
        if template_id:
            try:
                template = EmailTemplate.objects.get(id=template_id, user=request.user)
                campaign.email_template = template
            except EmailTemplate.DoesNotExist:
                pass
        
        campaign.save()
        
        # Update contacts if provided
        contact_ids = request.data.get('contact_ids')
        if contact_ids is not None:
            # Remove existing contacts
            CampaignContact.objects.filter(campaign=campaign).delete()
            
            # Add new contacts
            contacts = Contact.objects.filter(user=request.user, id__in=contact_ids)
            for contact in contacts:
                CampaignContact.objects.create(
                    campaign=campaign,
                    contact=contact
                )
        
        return Response({
            'id': campaign.id,
            'name': campaign.name,
            'success': True,
            'message': f"Campaign '{campaign.name}' updated successfully"
        })
    
    def delete(self, request, campaign_id):
        """Delete a campaign."""
        campaign = self.get_campaign(campaign_id, request.user)
        campaign_name = campaign.name
        campaign.delete()
        
        return Response({
            'success': True,
            'message': f"Campaign '{campaign_name}' deleted successfully"
        })

class RecentCampaignsAPIView(APIView):
    """API view to get recent campaigns for the dashboard."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return recent campaigns for the current user."""
        # Get the 5 most recent campaigns
        campaigns = Campaign.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        campaign_data = []
        for campaign in campaigns:
            campaign_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'template_name': campaign.email_template.name if campaign.email_template else None,
                'created_at': campaign.created_at.isoformat(),
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                'is_sent': campaign.is_sent,
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None
            })
        
        return Response(campaign_data)

class ListContactsAPIView(APIView):
    """API view to get contact count in a list."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return the number of contacts in a specified list."""
        list_id = request.GET.get('list_id')
        if not list_id:
            return Response({'error': 'List ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            contact_list = CampaignList.objects.get(id=list_id, user=request.user)
            contact_count = contact_list.contacts.count()
            
            return Response({
                'count': contact_count,
                'list_id': list_id,
                'list_name': contact_list.name
            })
        except CampaignList.DoesNotExist:
            return Response({'error': 'List not found'}, status=status.HTTP_404_NOT_FOUND)

class FilterContactsAPIView(APIView):
    """API view to get contact count based on filters."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Return the number of contacts matching the specified filters."""
        companies = request.data.get('companies', [])
        positions = request.data.get('positions', [])
        
        # Start with all contacts for this user
        contacts_query = Contact.objects.filter(user=request.user)
        
        # Apply filters
        if companies:
            contacts_query = contacts_query.filter(company__in=companies)
        if positions:
            contacts_query = contacts_query.filter(position__in=positions)
        
        # Get the count
        contact_count = contacts_query.count()
        
        return Response({
            'count': contact_count,
            'filters': {
                'companies': companies,
                'positions': positions
            }
        })
