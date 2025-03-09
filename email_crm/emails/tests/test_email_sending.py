import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from emails.models import EmailTemplate, SentEmail
from contacts.models import Contact
from django.test import Client
from django.utils import timezone
import datetime

"""
Tests for the email sending features.
These tests cover the scenarios described in:
- features/individual_email.feature
- features/bulk_email.feature
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
        username='emailuser',
        email='emailuser@example.com',
        password='emailpass123'
    )
    return user

@pytest.fixture
def authenticated_client(authenticated_user):
    """Get an authenticated API client."""
    client = APIClient()
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': 'emailuser', 'password': 'emailpass123'},
        format='json'
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, authenticated_user

@pytest.fixture
def authenticated_django_client(django_client, authenticated_user):
    """Get an authenticated Django test client."""
    django_client.login(username='emailuser', password='emailpass123')
    return django_client, authenticated_user

@pytest.fixture
def sample_contact(authenticated_user):
    """Create a sample contact for testing."""
    contact = Contact.objects.create(
        user=authenticated_user,
        name='John Smith',
        email='john@example.com',
        company='Acme Inc',
        position='Manager'
    )
    return contact

@pytest.fixture
def multiple_contacts(authenticated_user):
    """Create multiple contacts for testing bulk email functionality."""
    contacts = [
        Contact.objects.create(
            user=authenticated_user,
            name=f'Contact {i}',
            email=f'contact{i}@example.com',
            company=f'Company {i % 3}',  # Creates contacts at different companies
            position=f'Position {i % 2}'  # Creates contacts with different positions
        )
        for i in range(5)
    ]
    return contacts

@pytest.fixture
def sample_template(authenticated_user):
    """Create a sample email template for testing."""
    template = EmailTemplate.objects.create(
        user=authenticated_user,
        name='Welcome Email',
        subject='Welcome to {{company}}',
        body='Dear {{name}}, Welcome to {{company}}. We are excited to have you on board!'
    )
    return template

@pytest.mark.django_db
class TestIndividualEmailSending:
    """Test cases for the individual email sending feature.
    Corresponds to features/individual_email.feature
    """

    def test_send_individual_email(self, authenticated_client, sample_contact, sample_template):
        """
        Feature: Individual Email Sending
        Scenario: User sends an email to a contact
        Given I am logged in
        And I have contacts in my list
        And I have email templates available
        Given I am viewing a contact's details
        When I click the "Send Email" button
        And I select an email template
        And I click the "Send" button
        Then I should see a success message
        And the email should be recorded in the contact's activity history
        
        Tests the API endpoint for sending an individual email using a template.
        """
        client, user = authenticated_client
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Prepare email data
        email_data = {
            'template_id': sample_template.id,
            'subject': 'Welcome to Acme Inc',  # Can override template subject
            'body': None  # Use template body
        }
        
        # Send email
        response = client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.id}),
            email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check if email was recorded in the database
        assert SentEmail.objects.filter(user=user, contact=sample_contact).exists()
        
        # Check email fields
        sent_email = SentEmail.objects.get(user=user, contact=sample_contact)
        assert sent_email.subject == 'Welcome to Acme Inc'
        assert 'Welcome to Acme Inc' in sent_email.body
        assert 'Dear John Smith' in sent_email.body
        assert sent_email.template == sample_template
        
        # Check that the email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Welcome to Acme Inc'
        assert mail.outbox[0].to == ['john@example.com']

    def test_send_customized_email(self, authenticated_client, sample_contact, sample_template):
        """
        Feature: Individual Email Sending
        Scenario: User sends a customized email to a contact
        Given I am logged in
        And I have contacts in my list
        And I have email templates available
        Given I am viewing a contact's details
        When I click the "Send Email" button
        And I select an email template
        And I customize the email content
        And I click the "Send" button
        Then I should see a success message
        And the customized email should be sent to the contact
        
        Tests the API endpoint for sending a customized email to an individual contact.
        """
        client, user = authenticated_client
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Prepare customized email data
        custom_email_data = {
            'template_id': sample_template.id,
            'subject': 'Special Welcome to Acme Inc',  # Customized subject
            'body': 'Dear John Smith, This is a completely customized welcome message for you. Welcome aboard!'  # Customized body
        }
        
        # Send email
        response = client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.id}),
            custom_email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check if email was recorded in the database
        assert SentEmail.objects.filter(user=user, contact=sample_contact).exists()
        
        # Check email fields
        sent_email = SentEmail.objects.get(user=user, contact=sample_contact)
        assert sent_email.subject == 'Special Welcome to Acme Inc'
        assert sent_email.body == 'Dear John Smith, This is a completely customized welcome message for you. Welcome aboard!'
        assert sent_email.template == sample_template  # Still tracks the original template
        
        # Check that the email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Special Welcome to Acme Inc'
        assert mail.outbox[0].to == ['john@example.com']
        assert 'completely customized welcome message' in mail.outbox[0].body

    def test_email_variables_replacement(self, authenticated_client, sample_contact, sample_template):
        """
        Feature: Individual Email Sending
        Scenario: User sends an email to a contact
        Given I am logged in
        And I have contacts in my list
        And I have email templates available
        Given I am viewing a contact's details
        When I click the "Send Email" button
        And I select an email template
        And I click the "Send" button
        Then the template variables should be replaced with contact data
        
        Tests that template variables are properly replaced with contact data.
        """
        client, user = authenticated_client
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Prepare email data using just the template (no overrides)
        email_data = {
            'template_id': sample_template.id
        }
        
        # Send email
        response = client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.id}),
            email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that variables were replaced
        sent_email = SentEmail.objects.get(user=user, contact=sample_contact)
        assert sent_email.subject == 'Welcome to Acme Inc'  # {{company}} replaced
        assert 'Dear John Smith' in sent_email.body  # {{name}} replaced
        assert 'Welcome to Acme Inc' in sent_email.body  # {{company}} replaced
        
        # Check the sent email
        assert len(mail.outbox) == 1
        assert 'Dear John Smith' in mail.outbox[0].body
        assert 'Welcome to Acme Inc' in mail.outbox[0].body


@pytest.mark.django_db
class TestBulkEmailSending:
    """Test cases for the bulk email sending feature.
    Corresponds to features/bulk_email.feature
    """

    def test_bulk_email_sending(self, authenticated_client, multiple_contacts, sample_template):
        """
        Feature: Bulk Email Sending
        Scenario: User sends a bulk email to multiple contacts
        Given I am logged in
        And I have contacts in my list
        And I have email templates available
        Given I am on the contacts page
        When I select multiple contacts
        And I click the "Bulk Email" button
        And I select an email template
        And I click the "Send" button
        Then I should see a confirmation message
        And the emails should be queued for sending
        
        Tests the API endpoint for sending bulk emails.
        """
        client, user = authenticated_client
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Get IDs of all contacts
        contact_ids = [contact.id for contact in multiple_contacts]
        
        # Prepare bulk email data
        bulk_email_data = {
            'template_id': sample_template.id,
            'contact_ids': contact_ids
        }
        
        # Send bulk email
        response = client.post(
            reverse('emails:bulk-send-email'),
            bulk_email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the response contains success message
        assert 'success' in response.data
        assert 'emails queued for sending' in response.data['message']
        
        # Check that all emails were recorded in the database
        assert SentEmail.objects.filter(user=user).count() == len(contact_ids)
        
        # Check that all emails were sent
        assert len(mail.outbox) == len(contact_ids)
        
        # Check that each contact received their email with proper variable substitution
        for contact in multiple_contacts:
            # Find the sent email for this contact
            sent_email = SentEmail.objects.get(user=user, contact=contact)
            
            # Check variable replacement in subject and body
            assert sent_email.subject == f'Welcome to {contact.company}'
            assert f'Dear {contact.name}' in sent_email.body
            assert f'Welcome to {contact.company}' in sent_email.body
            
            # Check that the email was actually sent to the contact
            matching_emails = [email for email in mail.outbox if contact.email in email.to]
            assert len(matching_emails) == 1
            assert matching_emails[0].subject == f'Welcome to {contact.company}'

    def test_scheduled_bulk_email(self, authenticated_client, multiple_contacts, sample_template):
        """
        Feature: Bulk Email Sending
        Scenario: User schedules a bulk email for later delivery
        Given I am logged in
        And I have contacts in my list
        And I have email templates available
        Given I am on the contacts page
        When I select multiple contacts
        And I click the "Bulk Email" button
        And I select an email template
        And I set a future delivery date
        And I click the "Schedule" button
        Then I should see a confirmation message
        And the emails should be scheduled for the specified time
        
        Tests the API endpoint for scheduling bulk emails for future delivery.
        """
        client, user = authenticated_client
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Get IDs of all contacts
        contact_ids = [contact.id for contact in multiple_contacts]
        
        # Set scheduled time (1 hour in the future)
        scheduled_time = timezone.now() + datetime.timedelta(hours=1)
        scheduled_time_str = scheduled_time.isoformat()
        
        # Prepare scheduled bulk email data
        scheduled_email_data = {
            'template_id': sample_template.id,
            'contact_ids': contact_ids,
            'scheduled_time': scheduled_time_str
        }
        
        # Schedule bulk email
        response = client.post(
            reverse('emails:bulk-send-email'),
            scheduled_email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the response contains success message
        assert 'success' in response.data
        assert 'emails scheduled for sending' in response.data['message']
        
        # Check that all emails were recorded in the database
        assert SentEmail.objects.filter(user=user).count() == len(contact_ids)
        
        # Check that emails were scheduled correctly
        for sent_email in SentEmail.objects.filter(user=user):
            assert sent_email.scheduled_time is not None
            # Allow for small difference in stored time due to serialization/deserialization
            time_diff = abs((sent_email.scheduled_time - scheduled_time).total_seconds())
            assert time_diff < 60  # Within a minute
            
            # Check that email hasn't been sent yet
            assert sent_email.sent_at is None
            
        # Check that no emails were sent immediately
        assert len(mail.outbox) == 0

    def test_bulk_email_access_protection(self, api_client, multiple_contacts, sample_template):
        """
        Feature: Bulk Email Sending
        Background: I am logged in
        
        Tests that bulk email endpoints are protected and require authentication.
        """
        # Get IDs of all contacts
        contact_ids = [contact.id for contact in multiple_contacts]
        
        # Prepare bulk email data
        bulk_email_data = {
            'template_id': sample_template.id,
            'contact_ids': contact_ids
        }
        
        # Attempt to send bulk email without authentication
        response = api_client.post(
            reverse('emails:bulk-send-email'),
            bulk_email_data,
            format='json'
        )
        
        # Check that access is denied
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 