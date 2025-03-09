from django.shortcuts import render
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Contact
from .serializers import ContactSerializer
from django.db.models import Q

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
