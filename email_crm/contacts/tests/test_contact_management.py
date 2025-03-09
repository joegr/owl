import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from contacts.models import Contact

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_user():
    """Create and authenticate a user."""
    user = User.objects.create_user(
        username='contactuser',
        email='contact@example.com',
        password='contactpass123'
    )
    return user

@pytest.fixture
def authenticated_client(authenticated_user):
    """Get an authenticated API client."""
    client = APIClient()
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': 'contactuser', 'password': 'contactpass123'},
        format='json'
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, authenticated_user

@pytest.fixture
def sample_contact(authenticated_user):
    """Create a sample contact for testing."""
    contact = Contact.objects.create(
        user=authenticated_user,
        name='John Doe',
        email='john@example.com',
        phone='+1234567890',
        company='Acme Inc',
        position='Manager',
        notes='Test contact'
    )
    return contact

@pytest.mark.django_db
class TestContactManagement:
    """Test cases for contact management feature."""

    def test_add_contact(self, authenticated_client):
        """
        Scenario: User adds a new contact
        Given I am on the contacts page
        When I click the "Add Contact" button
        And I fill in the contact details
        And I click the "Save" button
        Then I should see a success message
        And the contact should appear in my contact list
        """
        client, user = authenticated_client
        
        # Initial count of contacts
        initial_count = Contact.objects.filter(user=user).count()
        
        # Contact data
        contact_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '+9876543210',
            'company': 'Widget Corp',
            'position': 'Developer',
            'notes': 'New contact for testing'
        }
        
        # Add contact
        response = client.post(
            reverse('contacts:contact-list'),
            contact_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that contact was created
        assert Contact.objects.filter(user=user).count() == initial_count + 1
        
        # Check that contact has correct data
        new_contact = Contact.objects.get(email='jane@example.com')
        assert new_contact.name == 'Jane Smith'
        assert new_contact.company == 'Widget Corp'
        assert new_contact.user == user

    def test_view_contact_details(self, authenticated_client, sample_contact):
        """
        Scenario: User views contact details
        Given I have contacts in my contact list
        When I click on a contact name
        Then I should see the contact's details
        """
        client, user = authenticated_client
        
        # View contact details
        response = client.get(
            reverse('contacts:contact-detail', kwargs={'pk': sample_contact.pk})
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check contact details in response
        assert response.data['name'] == 'John Doe'
        assert response.data['email'] == 'john@example.com'
        assert response.data['company'] == 'Acme Inc'

    def test_edit_contact(self, authenticated_client, sample_contact):
        """
        Scenario: User edits a contact
        Given I am viewing a contact's details
        When I click the "Edit" button
        And I modify the contact's details
        And I click the "Save" button
        Then I should see a success message
        And the contact should display the updated information
        """
        client, user = authenticated_client
        
        # Updated contact data
        updated_data = {
            'name': 'John Doe Jr.',
            'email': 'johnjr@example.com',
            'phone': '+1234567899',
            'company': 'Acme Corporation',
            'position': 'Senior Manager',
            'notes': 'Updated test contact'
        }
        
        # Update contact
        response = client.put(
            reverse('contacts:contact-detail', kwargs={'pk': sample_contact.pk}),
            updated_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that contact was updated
        sample_contact.refresh_from_db()
        assert sample_contact.name == 'John Doe Jr.'
        assert sample_contact.email == 'johnjr@example.com'
        assert sample_contact.company == 'Acme Corporation'

    def test_delete_contact(self, authenticated_client, sample_contact):
        """
        Scenario: User deletes a contact
        Given I am viewing a contact's details
        When I click the "Delete" button
        And I confirm the deletion
        Then I should see a success message
        And the contact should no longer appear in my contact list
        """
        client, user = authenticated_client
        
        # Initial count of contacts
        initial_count = Contact.objects.filter(user=user).count()
        
        # Delete contact
        response = client.delete(
            reverse('contacts:contact-detail', kwargs={'pk': sample_contact.pk})
        )
        
        # Check response status
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that contact was deleted
        assert Contact.objects.filter(user=user).count() == initial_count - 1
        assert not Contact.objects.filter(pk=sample_contact.pk).exists()

    def test_contact_list(self, authenticated_client, sample_contact):
        """
        Test listing all contacts for a user.
        """
        client, user = authenticated_client
        
        # Create a second contact
        Contact.objects.create(
            user=user,
            name='Alice Johnson',
            email='alice@example.com',
            company='Tech Corp'
        )
        
        # Get contact list
        response = client.get(reverse('contacts:contact-list'))
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that both contacts are in the list
        assert len(response.data) == 2
        
        # Check contact names in response
        contact_names = [contact['name'] for contact in response.data]
        assert 'John Doe' in contact_names
        assert 'Alice Johnson' in contact_names

    def test_contact_privacy(self, authenticated_client, sample_contact):
        """
        Test that users can only access their own contacts.
        """
        # Create a second user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create a contact for the second user
        other_contact = Contact.objects.create(
            user=other_user,
            name='Private Contact',
            email='private@example.com'
        )
        
        client, user = authenticated_client
        
        # Try to view the other user's contact
        response = client.get(
            reverse('contacts:contact-detail', kwargs={'pk': other_contact.pk})
        )
        
        # Check that access is denied (404 because we filter queryset)
        assert response.status_code == status.HTTP_404_NOT_FOUND 