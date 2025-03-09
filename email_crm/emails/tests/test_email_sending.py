import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from emails.models import EmailTemplate, SentEmail
from contacts.models import Contact

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
            name='Jane Doe',
            email='jane@example.com',
            company='Widget Corp'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Michael Johnson',
            email='michael@example.com',
            company='Tech Inc'
        ),
        Contact.objects.create(
            user=authenticated_user,
            name='Emily Brown',
            email='emily@example.com',
            company='Acme Inc'
        )
    ]
    return contacts

@pytest.fixture
def sample_template(authenticated_user):
    """Create a sample email template for testing."""
    template = EmailTemplate.objects.create(
        user=authenticated_user,
        name='Test Template',
        subject='Test Subject',
        body='Hello {{name}}, This is a test email for {{company}}.'
    )
    return template

@pytest.mark.django_db
class TestEmailSending:
    """Test cases for email sending functionality."""

    def test_send_individual_email(self, authenticated_client, sample_contact, sample_template):
        """
        Scenario: User sends an email to a contact
        Given I am viewing a contact's details
        When I click the "Send Email" button
        And I select an email template
        And I click the "Send" button
        Then I should see a success message
        And the email should be recorded in the contact's activity history
        """
        client, user = authenticated_client
        
        # Clear the test outbox
        mail.outbox = []
        
        # Initial count of sent emails
        initial_count = SentEmail.objects.count()
        
        # Send email
        response = client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.pk}),
            {'template_id': sample_template.pk},
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that a SentEmail record was created
        assert SentEmail.objects.count() == initial_count + 1
        
        # Get the sent email record
        sent_email = SentEmail.objects.latest('sent_at')
        assert sent_email.user == user
        assert sent_email.contact == sample_contact
        assert sent_email.template == sample_template
        
        # Check that email variables were replaced
        assert sample_contact.name in sent_email.body
        assert sample_contact.company in sent_email.body
        
        # Check that an email was actually sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_contact.email]
        assert mail.outbox[0].subject == sample_template.subject

    def test_send_customized_email(self, authenticated_client, sample_contact):
        """
        Test sending a customized email without using a template.
        """
        client, user = authenticated_client
        
        # Clear the test outbox
        mail.outbox = []
        
        # Custom email data
        email_data = {
            'subject': 'Custom Subject',
            'body': f'Hello {sample_contact.name}, this is a custom email just for you.'
        }
        
        # Send email
        response = client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.pk}),
            email_data,
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that the email was sent with the custom content
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Custom Subject'
        assert sample_contact.name in mail.outbox[0].body

    def test_bulk_email_sending(self, authenticated_client, multiple_contacts, sample_template):
        """
        Scenario: User sends a bulk email to multiple contacts
        Given I am on the contacts page
        When I select multiple contacts
        And I click the "Bulk Email" button
        And I select an email template
        And I click the "Send" button
        Then I should see a confirmation message
        And the emails should be queued for sending
        """
        client, user = authenticated_client
        
        # Clear the test outbox
        mail.outbox = []
        
        # Initial count of sent emails
        initial_count = SentEmail.objects.count()
        
        # Get contact IDs
        contact_ids = [contact.pk for contact in multiple_contacts]
        
        # Send bulk email
        response = client.post(
            reverse('emails:bulk-send-email'),
            {
                'contact_ids': contact_ids,
                'template_id': sample_template.pk
            },
            format='json'
        )
        
        # Check response status
        assert response.status_code == status.HTTP_200_OK
        
        # Check that SentEmail records were created for each contact
        assert SentEmail.objects.count() == initial_count + len(multiple_contacts)
        
        # Check that emails were actually sent
        assert len(mail.outbox) == len(multiple_contacts)
        
        # Check that emails were sent to all contacts
        sent_to = [email.to[0] for email in mail.outbox]
        for contact in multiple_contacts:
            assert contact.email in sent_to

    def test_email_variables_replacement(self, authenticated_client, sample_contact, sample_template):
        """Test that template variables are correctly replaced with contact information."""
        client, user = authenticated_client
        
        # Clear the test outbox
        mail.outbox = []
        
        # Send email
        client.post(
            reverse('emails:send-email', kwargs={'contact_id': sample_contact.pk}),
            {'template_id': sample_template.pk},
            format='json'
        )
        
        # Check variable replacement in the sent email
        sent_email = SentEmail.objects.latest('sent_at')
        assert sample_contact.name in sent_email.body
        assert sample_contact.company in sent_email.body
        assert '{{name}}' not in sent_email.body
        assert '{{company}}' not in sent_email.body 