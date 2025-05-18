from django.shortcuts import render, get_object_or_404
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from .models import Contact
from .serializers import ContactSerializer
from django.db.models import Q
from emails.models import SentEmail
from rest_framework.decorators import api_view, permission_classes
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from .forms import ContactForm

# Create your views here.

class ContactListCreateView(generics.ListCreateAPIView):
    """
    API view to list all contacts (with optional filtering) and create new contacts.
    
    GET: List all contacts belonging to the current user
    POST: Create a new contact
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return filtered contacts belonging to the current user."""
        queryset = Contact.objects.filter(user=self.request.user)
        
        # Filter by company if provided
        company = self.request.query_params.get('company', None)
        if company:
            queryset = queryset.filter(company=company)
            
        # Filter by position if provided
        position = self.request.query_params.get('position', None)
        if position:
            queryset = queryset.filter(position=position)
            
        # Filter by email domain if provided
        email_domain = self.request.query_params.get('email_domain', None)
        if email_domain:
            queryset = queryset.filter(email__endswith=email_domain)
            
        return queryset
    
    def perform_create(self, serializer):
        """Set the user to the current authenticated user when creating a contact."""
        serializer.save(user=self.request.user)

class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a specific contact.
    
    GET: Retrieve a contact
    PUT/PATCH: Update a contact
    DELETE: Delete a contact
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only contacts belonging to the current user."""
        return Contact.objects.filter(user=self.request.user)

class ContactSearchView(generics.ListAPIView):
    """
    API view to search contacts based on a query parameter.
    
    GET: Search contacts with a query parameter 'q'
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Search contacts by name, email, or company."""
        queryset = Contact.objects.filter(user=self.request.user)
        search_query = self.request.query_params.get('q', None)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(company__icontains=search_query) |
                Q(position__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Apply additional filters
        # Filter by company if provided
        company = self.request.query_params.get('company', None)
        if company:
            queryset = queryset.filter(company=company)
            
        # Filter by position if provided
        position = self.request.query_params.get('position', None)
        if position:
            queryset = queryset.filter(position=position)
        
        return queryset

# Template Views
@login_required
def contact_detail_view(request, contact_id):
    """View to display the contact details page."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    emails = SentEmail.objects.filter(contact=contact, user=request.user).order_by('-sent_at')[:10]
    return render(request, 'contacts/contact_detail.html', {'contact': contact, 'emails': emails})

@login_required
def contact_edit_view(request, contact_id):
    """View to display and process the contact edit form."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated successfully!")
            return redirect('contacts:view', contact_id=contact.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm(instance=contact)
    
    return render(request, 'contacts/contact_form.html', {'form': form, 'contact': contact, 'action': 'Edit'})

@login_required
def contact_add_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, "Contact added successfully!")
            return redirect('contacts:view', contact_id=contact.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()
    
    return render(request, 'contacts/contact_form.html', {'form': form, 'action': 'Add'})

@login_required
def contact_list_view(request):
    """View to display all contacts with filtering options."""
    return render(request, 'contacts/contact_list.html')

@login_required
def contact_delete_view(request, contact_id):
    """View to confirm and process contact deletion."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        contact_name = contact.name
        contact.delete()
        messages.success(request, f"Contact '{contact_name}' has been deleted.")
        return redirect('contacts:list')
    
    return render(request, 'contacts/contact_delete.html', {'contact': contact})

# API View for contact's emails
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contact_emails_view(request, contact_id):
    """API view to get emails sent to a specific contact."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    emails = SentEmail.objects.filter(contact=contact, user=request.user).order_by('-sent_at')[:10]
    
    email_data = []
    for email in emails:
        email_data.append({
            'id': email.id,
            'subject': email.subject,
            'sent_at': email.sent_at,
            'opened': email.opened,
            'clicked': email.clicked
        })
    
    return Response({'emails': email_data})
