import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from contacts.models import Contact

@pytest.fixture
def authenticated_user():
    """Create a user for testing."""
    user = User.objects.create_user(
        username='filteruser',
        email='filter@example.com',
        password='filterpass123'
    )
    return user

@pytest.fixture
def authenticated_client(authenticated_user):
    """Get an authenticated API client."""
    client = APIClient()
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': 'filteruser', 'password': 'filterpass123'},
        format='json'
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, authenticated_user

@pytest.fixture
def multiple_contacts(authenticated_user):
    """Create multiple contacts for testing filtering functionality."""
    contacts = [
        Contact.objects.create(
            user=authenticated_user,
            name='John Smith',
            email='john@example.com',
            company='Tech Corp',
            position='Developer'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Jane Smith',
            email='jane@example.com',
            company='Acme Inc',
            position='Manager'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Michael Johnson',
            email='michael@techinc.com',
            company='Tech Inc',
            position='CEO'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Emily Brown',
            email='emily@acmeinc.com',
            company='Acme Inc',
            position='Designer'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='David Wilson',
            email='david@example.com',
            company='Widget Corp',
            position='Engineer'
        )
    ]
    return contacts

@pytest.mark.django_db
class TestContactFiltering:
    """Test cases for contact filtering and search functionality."""

    def test_filter_contacts_by_company(self, authenticated_client, multiple_contacts):
        """
        Scenario: User filters contacts by criteria
        Given I am on the contacts page
        When I apply filters based on specific criteria
        Then I should see only the contacts that match my filter criteria
        """
        client, user = authenticated_client
        
        # Filter contacts by company
        response = client.get(
            f"{reverse('contacts:contact-list')}?company=Acme Inc"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only contacts from Acme Inc are returned
        assert len(response.data) == 2
        
        # Check company names in response
        companies = [contact['company'] for contact in response.data]
        assert all(company == 'Acme Inc' for company in companies)
        
        # Check that the correct contacts are returned
        names = [contact['name'] for contact in response.data]
        assert 'Jane Smith' in names
        assert 'Emily Brown' in names

    def test_search_contacts(self, authenticated_client, multiple_contacts):
        """
        Scenario: User searches for a contact
        Given I am on the contacts page
        When I enter a search term in the search box
        Then I should see contacts that match my search term
        """
        client, user = authenticated_client
        
        # Search for contacts with 'tech' in name, email, or company
        response = client.get(
            reverse('contacts:contact-search') + '?q=tech'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the correct contacts are returned
        assert len(response.data) == 2
        
        # Check names in response
        names = [contact['name'] for contact in response.data]
        assert 'John Smith' in names  # from Tech Corp
        assert 'Michael Johnson' in names  # from Tech Inc

    def test_combined_search_and_filter(self, authenticated_client, multiple_contacts):
        """Test combining search and filter parameters."""
        client, user = authenticated_client
        
        # Search for contacts with 'smith' in name, email, or company
        # and position is 'Developer'
        response = client.get(
            reverse('contacts:contact-search') + '?q=smith&position=Developer'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only the correct contact is returned
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'John Smith'
        assert response.data[0]['position'] == 'Developer'

    def test_empty_search_results(self, authenticated_client, multiple_contacts):
        """Test search with no matching results."""
        client, user = authenticated_client
        
        # Search for a term that won't match any contacts
        response = client.get(
            reverse('contacts:contact-search') + '?q=nonexistent'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that no contacts are returned
        assert len(response.data) == 0 