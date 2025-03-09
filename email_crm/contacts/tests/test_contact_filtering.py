import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from contacts.models import Contact
from django.test import Client

"""
Tests for the contact filtering and search feature.
These tests cover the scenarios described in features/contact_filtering.feature
"""

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def django_client():
    return Client()

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
def authenticated_django_client(django_client, authenticated_user):
    """Get an authenticated Django test client."""
    django_client.login(username='filteruser', password='filterpass123')
    return django_client, authenticated_user

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
            name='Alice Johnson',
            email='alice@example.com',
            company='Tech Corp',
            position='Designer'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Bob Williams',
            email='bob@example.com',
            company='XYZ Ltd',
            position='Developer'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Charlie Brown',
            email='charlie@example.com',
            company='Acme Inc',
            position='Director'
        )
    ]
    return contacts

@pytest.mark.django_db
class TestContactFiltering:
    """Test cases for the contact filtering and search feature.
    Corresponds to features/contact_filtering.feature
    """

    def test_filter_contacts_by_company(self, authenticated_client, multiple_contacts):
        """
        Feature: Contact Filtering and Search
        Scenario: User filters contacts by criteria
        Given I am logged in
        And I have multiple contacts in my list
        Given I am on the contacts page
        When I apply filters based on specific criteria
        Then I should see only the contacts that match my filter criteria
        
        Tests filtering contacts by company.
        """
        client, user = authenticated_client
        
        # Filter by Tech Corp company
        response = client.get(
            f"{reverse('contacts:contact-list')}?company=Tech Corp"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only Tech Corp contacts are returned
        assert len(response.data) == 2
        companies = [contact['company'] for contact in response.data]
        assert all(company == 'Tech Corp' for company in companies)
        
        # Filter by Acme Inc company
        response = client.get(
            f"{reverse('contacts:contact-list')}?company=Acme Inc"
        )
        
        # Check that only Acme Inc contacts are returned
        assert len(response.data) == 2
        companies = [contact['company'] for contact in response.data]
        assert all(company == 'Acme Inc' for company in companies)

    def test_filter_contacts_by_position(self, authenticated_client, multiple_contacts):
        """
        Feature: Contact Filtering and Search
        Scenario: User filters contacts by criteria
        Given I am logged in
        And I have multiple contacts in my list
        Given I am on the contacts page
        When I apply filters based on specific criteria
        Then I should see only the contacts that match my filter criteria
        
        Tests filtering contacts by position.
        """
        client, user = authenticated_client
        
        # Filter by Developer position
        response = client.get(
            f"{reverse('contacts:contact-list')}?position=Developer"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only Developer contacts are returned
        assert len(response.data) == 2
        positions = [contact['position'] for contact in response.data]
        assert all(position == 'Developer' for position in positions)

    def test_search_contacts(self, authenticated_client, multiple_contacts):
        """
        Feature: Contact Filtering and Search
        Scenario: User searches for a contact
        Given I am logged in
        And I have multiple contacts in my list
        Given I am on the contacts page
        When I enter a search term in the search box
        Then I should see contacts that match my search term
        
        Tests searching contacts by name.
        """
        client, user = authenticated_client
        
        # Search for "Smith" in name
        response = client.get(
            f"{reverse('contacts:contact-list')}?search=Smith"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only Smith contacts are returned
        assert len(response.data) == 2
        names = [contact['name'] for contact in response.data]
        assert all('Smith' in name for name in names)
        
        # Search for "alice" in name or email
        response = client.get(
            f"{reverse('contacts:contact-list')}?search=alice"
        )
        
        # Check that only Alice contact is returned
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Alice Johnson'

    def test_combined_search_and_filter(self, authenticated_client, multiple_contacts):
        """
        Feature: Contact Filtering and Search
        Scenario: User filters contacts by criteria
        And User searches for a contact
        Given I am logged in
        And I have multiple contacts in my list
        Given I am on the contacts page
        When I apply filters based on specific criteria
        And I enter a search term in the search box
        Then I should see only the contacts that match both my filter criteria and search term
        
        Tests combining search and filter functionality.
        """
        client, user = authenticated_client
        
        # Search for "Smith" AND filter by "Tech Corp" company
        response = client.get(
            f"{reverse('contacts:contact-list')}?search=Smith&company=Tech Corp"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that only John Smith is returned (Smith name in Tech Corp)
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'John Smith'
        assert response.data[0]['company'] == 'Tech Corp'

    def test_empty_search_results(self, authenticated_client, multiple_contacts):
        """
        Feature: Contact Filtering and Search
        Scenario: User searches for a contact
        Given I am logged in
        And I have multiple contacts in my list
        Given I am on the contacts page
        When I enter a search term in the search box that doesn't match any contacts
        Then I should see an empty list of results
        
        Tests that searches with no matching results return an empty list.
        """
        client, user = authenticated_client
        
        # Search for non-existent term
        response = client.get(
            f"{reverse('contacts:contact-list')}?search=NonExistentTerm"
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that no contacts are returned
        assert len(response.data) == 0

    def test_filter_access_protection(self, api_client):
        """
        Feature: Contact Filtering and Search
        Background: I am logged in
        
        Tests that filtering and searching endpoints are protected and require authentication.
        """
        # Attempt to access contact list with filters without authentication
        response = api_client.get(
            f"{reverse('contacts:contact-list')}?company=Tech Corp"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Attempt to search without authentication
        response = api_client.get(
            f"{reverse('contacts:contact-list')}?search=Smith"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 