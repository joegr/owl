import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
import datetime
from contacts.models import Contact
from emails.models import EmailTemplate, SentEmail
from dashboard.models import Activity
from django.test import Client

"""
Tests for the dashboard feature.
These tests cover the scenarios described in features/dashboard.feature
"""

@pytest.fixture
def authenticated_user():
    """Create a user for testing."""
    user = User.objects.create_user(
        username='dashboarduser',
        email='dashboard@example.com',
        password='dashboardpass123'
    )
    return user

@pytest.fixture
def django_client():
    return Client()

@pytest.fixture
def authenticated_client(authenticated_user):
    """Get an authenticated API client."""
    client = APIClient()
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': 'dashboarduser', 'password': 'dashboardpass123'},
        format='json'
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, authenticated_user

@pytest.fixture
def authenticated_django_client(django_client, authenticated_user):
    """Get an authenticated Django test client."""
    django_client.login(username='dashboarduser', password='dashboardpass123')
    return django_client, authenticated_user

@pytest.fixture
def dashboard_data(authenticated_user):
    """Create sample data for dashboard testing."""
    # Create contacts
    contacts = []
    for i in range(5):
        contact = Contact.objects.create(
            user=authenticated_user,
            name=f'Contact {i}',
            email=f'contact{i}@example.com',
            company='Test Company'
        )
        contacts.append(contact)
    
    # Create email template
    template = EmailTemplate.objects.create(
        user=authenticated_user,
        name='Test Template',
        subject='Test Subject',
        body='Test Body Content'
    )
    
    # Create sent emails with different statuses
    sent_emails = []
    for i, contact in enumerate(contacts):
        opened = i % 2 == 0  # Every other email is opened
        clicked = i % 3 == 0  # Every third email is clicked
        
        # Create one email today
        if i == 0:
            sent_at = timezone.now()
        # Create one email yesterday
        elif i == 1:
            sent_at = timezone.now() - datetime.timedelta(days=1)
        # Create one email last week
        else:
            sent_at = timezone.now() - datetime.timedelta(days=i+3)
            
        email = SentEmail.objects.create(
            user=authenticated_user,
            contact=contact,
            subject=f'Test Email {i}',
            body=f'Email content {i}',
            sent_at=sent_at,
            template=template if i % 2 == 0 else None,
            opened=opened,
            clicked=clicked
        )
        sent_emails.append(email)
    
    # Create activities
    activities = []
    for i in range(10):
        activity_type = 'email_sent' if i % 3 == 0 else 'contact_created' if i % 3 == 1 else 'template_created'
        
        activity = Activity.objects.create(
            user=authenticated_user,
            activity_type=activity_type,
            description=f'Activity {i}: {activity_type}',
            timestamp=timezone.now() - datetime.timedelta(hours=i)
        )
        activities.append(activity)
    
    return {
        'contacts': contacts,
        'template': template,
        'sent_emails': sent_emails,
        'activities': activities
    }

@pytest.mark.django_db
class TestDashboard:
    """Test cases for the dashboard feature.
    Corresponds to features/dashboard.feature
    """
    
    def test_dashboard_summary(self, authenticated_client, dashboard_data):
        """
        Feature: CRM Dashboard
        Scenario: User views dashboard
        Given I am logged in
        Given I am on the dashboard page
        Then I should see summary information including:
          | Metric                | Type    |
          | Total Contacts        | Number  |
          | Emails Sent (Today)   | Number  |
          | Open Rate (Average)   | Percent |
          | Recent Activities     | List    |
        
        Tests the API endpoint that provides dashboard summary data.
        """
        client, user = authenticated_client
        
        # Access the dashboard data endpoint
        response = client.get(reverse('dashboard:data'))
        
        # Check if request was successful
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all required dashboard components are present
        data = response.data
        assert 'contact_count' in data
        assert 'total_emails_sent' in data
        assert 'emails_today' in data
        assert 'open_rate' in data
        assert 'recent_activities' in data
        assert 'recent_emails' in data
        
        # Verify the values match our test data
        assert data['contact_count'] == 5  # We created 5 contacts
        assert data['total_emails_sent'] == 5  # We created 5 emails
        assert data['emails_today'] == 1  # One email was sent today
        
        # Verify open rate calculation
        # 3 out of 5 emails were opened (i % 2 == 0)
        expected_open_rate = 60.0  # (3/5 * 100)
        assert data['open_rate'] == expected_open_rate
        
        # Check that recent activities are returned
        assert len(data['recent_activities']) > 0
        
        # Check that recent emails are returned
        assert len(data['recent_emails']) > 0

    def test_dashboard_view(self, authenticated_django_client, dashboard_data):
        """
        Feature: CRM Dashboard
        Scenario: User views dashboard
        Given I am logged in
        Given I am on the dashboard page
        Then I should see summary information
        
        Tests the actual dashboard view/template.
        """
        client, user = authenticated_django_client
        
        # Access the dashboard page
        response = client.get(reverse('dashboard:dashboard'))
        
        # Check if request was successful
        assert response.status_code == 200
        
        # Verify the correct template is used
        assert 'dashboard/dashboard.html' in [template.name for template in response.templates]

    def test_dashboard_stats(self, authenticated_client, dashboard_data):
        """
        Feature: CRM Dashboard
        Scenario: User views dashboard
        Given I am logged in
        Given I am on the dashboard page
        Then I should see summary information
        
        Tests the detailed stats API endpoint.
        """
        client, user = authenticated_client
        
        # Access the dashboard stats endpoint
        response = client.get(reverse('dashboard:stats'))
        
        # Check if request was successful
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all required stats components are present
        data = response.data
        assert 'emails_per_day' in data
        assert 'top_contacts' in data
        assert 'template_stats' in data
        assert 'company_distribution' in data

    def test_navigation_from_dashboard(self, authenticated_django_client, dashboard_data):
        """
        Feature: CRM Dashboard
        Scenario: User navigates to different sections from dashboard
        Given I am on the dashboard page
        When I click on a dashboard widget
        Then I should be taken to the corresponding detailed section
        
        Tests that links on the dashboard navigate to the correct places.
        """
        client, user = authenticated_django_client
        
        # Access the dashboard page
        dashboard_response = client.get(reverse('dashboard:dashboard'))
        assert dashboard_response.status_code == 200
        
        # Test navigation to contacts
        contacts_response = client.get('/contacts/')
        assert contacts_response.status_code == 200
        
        # Test navigation to email templates
        templates_response = client.get('/emails/templates/')
        assert templates_response.status_code == 200
        
        # Test navigation to analytics
        analytics_response = client.get('/emails/analytics/')
        assert analytics_response.status_code == 200

    def test_recent_activities(self, authenticated_client, dashboard_data):
        """
        Feature: CRM Dashboard
        Scenario: User views dashboard
        Given I am logged in
        Given I am on the dashboard page
        Then I should see summary information including recent activities
        
        Tests the recent activities API endpoint.
        """
        client, user = authenticated_client
        
        # Access the recent activities endpoint
        response = client.get(reverse('dashboard:recent-activities'))
        
        # Check if request was successful
        assert response.status_code == status.HTTP_200_OK
        
        # Verify activities are returned
        data = response.data
        assert 'activities' in data
        assert len(data['activities']) > 0
        
        # Verify activity structure
        activity = data['activities'][0]
        assert 'id' in activity
        assert 'activity_type' in activity
        assert 'description' in activity
        assert 'timestamp' in activity

    def test_dashboard_access_protection(self, api_client):
        """
        Feature: CRM Dashboard
        Background: I am logged in
        
        Tests that dashboard is protected and requires authentication.
        """
        # Attempt to access dashboard endpoints without authentication
        response = api_client.get(reverse('dashboard:data'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        response = api_client.get(reverse('dashboard:stats'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        response = api_client.get(reverse('dashboard:recent-activities'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.fixture
def api_client():
    return APIClient() 