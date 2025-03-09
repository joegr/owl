import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from emails.models import EmailTemplate
from django.test import Client

"""
Tests for the email template management feature.
These tests cover the scenarios described in features/email_templates.feature
"""

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def django_client():
    return Client()

@pytest.fixture
def test_user():
    user = User.objects.create_user(
        username='templateuser',
        email='template@example.com',
        password='templatepass123'
    )
    return user

@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """Get an authenticated API client."""
    response = api_client.post(
        reverse('token_obtain_pair'),
        {'username': 'templateuser', 'password': 'templatepass123'},
        format='json'
    )
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client, test_user

@pytest.fixture
def authenticated_django_client(django_client, test_user):
    """Get an authenticated Django test client."""
    django_client.login(username='templateuser', password='templatepass123')
    return django_client, test_user

@pytest.fixture
def email_templates(test_user):
    """Create sample email templates for testing."""
    templates = []
    for i in range(3):
        template = EmailTemplate.objects.create(
            user=test_user,
            name=f'Test Template {i}',
            subject=f'Test Subject {i}',
            body=f'Test Body Content {i} with placeholder {{name}}',
        )
        templates.append(template)
    return templates

@pytest.mark.django_db
class TestEmailTemplates:
    """Test cases for the email template management feature.
    Corresponds to features/email_templates.feature
    """

    def test_create_template_api(self, authenticated_api_client):
        """
        Feature: Email Template Management
        Scenario: User creates an email template
        Given I am logged in
        Given I am on the templates page
        When I click the "Create Template" button
        And I fill in the template details
        And I click the "Save" button
        Then I should see a success message
        And the template should appear in my templates list
        
        Tests the API endpoint for creating a template.
        """
        client, user = authenticated_api_client
        
        # Create template data
        template_data = {
            'name': 'New API Template',
            'subject': 'New API Subject',
            'body': 'New API Body Content with {{name}}',
        }
        
        # Post to create endpoint
        response = client.post(
            reverse('emails:template-list'),
            template_data,
            format='json'
        )
        
        # Check if creation was successful
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check if template was created with correct data
        template_id = response.data['id']
        template = EmailTemplate.objects.get(id=template_id)
        assert template.name == template_data['name']
        assert template.subject == template_data['subject']
        assert template.body == template_data['body']
        assert template.user == user

    def test_view_template_list_api(self, authenticated_api_client, email_templates):
        """
        Feature: Email Template Management
        Background: I have templates in my list
        
        Tests the API endpoint for listing templates.
        """
        client, user = authenticated_api_client
        
        # Get templates list
        response = client.get(reverse('emails:template-list'))
        
        # Check if request was successful
        assert response.status_code == status.HTTP_200_OK
        
        # Check if all templates are returned
        assert len(response.data) == len(email_templates)
        
        # Check template properties
        for template in response.data:
            assert 'id' in template
            assert 'name' in template
            assert 'subject' in template
            assert 'body' in template
            assert 'created_at' in template

    def test_edit_template_api(self, authenticated_api_client, email_templates):
        """
        Feature: Email Template Management
        Scenario: User edits an email template
        Given I have templates in my list
        When I select a template to edit
        And I modify the template content
        And I save the changes
        Then I should see a success message
        And the template should be updated
        
        Tests the API endpoint for editing a template.
        """
        client, user = authenticated_api_client
        
        # Select first template
        template = email_templates[0]
        
        # Updated data
        updated_data = {
            'name': 'Updated Template Name',
            'subject': 'Updated Subject Line',
            'body': 'Updated Body Content with {{name}}',
        }
        
        # Send update request
        response = client.put(
            reverse('emails:template-detail', args=[template.id]),
            updated_data,
            format='json'
        )
        
        # Check if update was successful
        assert response.status_code == status.HTTP_200_OK
        
        # Check if template was updated
        template.refresh_from_db()
        assert template.name == updated_data['name']
        assert template.subject == updated_data['subject']
        assert template.body == updated_data['body']

    def test_delete_template_api(self, authenticated_api_client, email_templates):
        """
        Feature: Email Template Management
        Scenario: User deletes an email template
        Given I have templates in my list
        When I select a template to delete
        And I confirm the deletion
        Then I should see a success message
        And the template should be removed from my list
        
        Tests the API endpoint for deleting a template.
        """
        client, user = authenticated_api_client
        
        # Select template to delete
        template_to_delete = email_templates[1]
        initial_count = EmailTemplate.objects.count()
        
        # Send delete request
        response = client.delete(
            reverse('emails:template-detail', args=[template_to_delete.id])
        )
        
        # Check if deletion was successful
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check if template was removed
        assert EmailTemplate.objects.count() == initial_count - 1
        
        # Check that the template doesn't exist anymore
        with pytest.raises(EmailTemplate.DoesNotExist):
            EmailTemplate.objects.get(id=template_to_delete.id)

    def test_template_access_protection(self, api_client, email_templates):
        """
        Feature: Email Template Management
        Background: I am logged in
        
        Tests that template endpoints are protected and require authentication.
        """
        # Attempt to access template endpoints without authentication
        response = api_client.get(reverse('emails:template-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to view a specific template
        response = api_client.get(
            reverse('emails:template-detail', args=[email_templates[0].id])
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to create a template
        response = api_client.post(
            reverse('emails:template-list'),
            {'name': 'Unauthorized Template', 'subject': 'Unauthorized', 'body': 'test'},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_template_ownership_protection(self, api_client, email_templates):
        """
        Feature: Email Template Management
        
        Tests that templates can only be accessed by their owner.
        """
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Authenticate as the other user
        response = api_client.post(
            reverse('token_obtain_pair'),
            {'username': 'otheruser', 'password': 'otherpass123'},
            format='json'
        )
        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Try to access a template that belongs to test_user
        response = api_client.get(
            reverse('emails:template-detail', args=[email_templates[0].id])
        )
        
        # Should return 404 since the template doesn't belong to this user
        assert response.status_code == status.HTTP_404_NOT_FOUND 