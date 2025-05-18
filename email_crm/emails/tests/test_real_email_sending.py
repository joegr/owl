import pytest
from django.urls import reverse
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from emails.models import EmailTemplate, SentEmail
from contacts.models import Contact
from django.test import override_settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def sample_contact(authenticated_client):
    _, user = authenticated_client
    return Contact.objects.create(
        user=user,
        name='John Smith',
        email='john@example.com',
        company='Acme Inc',
        position='CEO'
    )

@pytest.fixture
def sample_template(authenticated_client):
    _, user = authenticated_client
    return EmailTemplate.objects.create(
        user=user,
        name='Welcome Template',
        subject='Welcome to {{company}}',
        body='Dear {{name}},\n\nWelcome to {{company}}. We are excited to have you on board!'
    )

@pytest.mark.django_db
class TestRealEmailSending:
    """Test cases for verifying real email sending functionality."""

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.gmail.com',
        EMAIL_PORT=587,
        EMAIL_USE_TLS=True,
        EMAIL_HOST_USER=os.getenv('TEST_EMAIL_USER'),
        EMAIL_HOST_PASSWORD=os.getenv('TEST_EMAIL_PASSWORD'),
        DEFAULT_FROM_EMAIL=os.getenv('TEST_EMAIL_USER')
    )
    def test_real_email_sending(self, authenticated_client, sample_contact, sample_template):
        """
        Test that emails are actually being sent through the configured SMTP server.
        This test requires valid SMTP credentials in environment variables:
        - TEST_EMAIL_USER: The email address to send from
        - TEST_EMAIL_PASSWORD: The app password for the email account
        """
        client, user = authenticated_client
        
        # Skip test if credentials are not configured
        if not os.getenv('TEST_EMAIL_USER') or not os.getenv('TEST_EMAIL_PASSWORD'):
            pytest.skip("SMTP credentials not configured. Set TEST_EMAIL_USER and TEST_EMAIL_PASSWORD environment variables.")

        # Prepare email data
        email_data = {
            'template_id': sample_template.id,
            'subject': 'Test Real Email',
            'body': 'This is a test email to verify SMTP functionality.'
        }

        try:
            # Send email
            response = client.post(
                reverse('emails:send-email', kwargs={'contact_id': sample_contact.id}),
                email_data,
                format='json'
            )

            # Check response status
            assert response.status_code == status.HTTP_201_CREATED

            # Verify email was recorded in database
            sent_email = SentEmail.objects.get(user=user, contact=sample_contact)
            assert sent_email.subject == 'Test Real Email'
            assert sent_email.body == 'This is a test email to verify SMTP functionality.'

            # Verify SMTP connection and sending
            smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            smtp.starttls()
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = sample_contact.email
            msg['Subject'] = 'SMTP Test'
            msg.attach(MIMEText('Testing SMTP connection...'))

            # Send test message
            smtp.send_message(msg)
            smtp.quit()

            # If we get here, SMTP is working
            assert True

        except Exception as e:
            pytest.fail(f"SMTP test failed: {str(e)}")

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.gmail.com',
        EMAIL_PORT=587,
        EMAIL_USE_TLS=True,
        EMAIL_HOST_USER=os.getenv('TEST_EMAIL_USER'),
        EMAIL_HOST_PASSWORD=os.getenv('TEST_EMAIL_PASSWORD'),
        DEFAULT_FROM_EMAIL=os.getenv('TEST_EMAIL_USER')
    )
    def test_bulk_real_email_sending(self, authenticated_client, sample_contact, sample_template):
        """
        Test bulk email sending through the configured SMTP server.
        This test requires valid SMTP credentials in environment variables:
        - TEST_EMAIL_USER: The email address to send from
        - TEST_EMAIL_PASSWORD: The app password for the email account
        """
        client, user = authenticated_client
        
        # Skip test if credentials are not configured
        if not os.getenv('TEST_EMAIL_USER') or not os.getenv('TEST_EMAIL_PASSWORD'):
            pytest.skip("SMTP credentials not configured. Set TEST_EMAIL_USER and TEST_EMAIL_PASSWORD environment variables.")

        # Create additional test contacts
        contacts = [
            Contact.objects.create(
                user=user,
                name=f'Test User {i}',
                email=f'test{i}@example.com',
                company=f'Test Company {i}',
                position='Test Position'
            ) for i in range(3)
        ]
        contacts.append(sample_contact)  # Add the sample contact

        # Prepare bulk email data
        bulk_email_data = {
            'template_id': sample_template.id,
            'contact_ids': [contact.id for contact in contacts]
        }

        try:
            # Send bulk email
            response = client.post(
                reverse('emails:bulk-send-email'),
                bulk_email_data,
                format='json'
            )

            # Check response status
            assert response.status_code == status.HTTP_200_OK

            # Verify emails were recorded in database
            for contact in contacts:
                sent_email = SentEmail.objects.get(user=user, contact=contact)
                assert sent_email.template == sample_template
                assert 'Welcome to' in sent_email.subject
                assert contact.name in sent_email.body

            # Verify SMTP connection and sending
            smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            smtp.starttls()
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = sample_contact.email
            msg['Subject'] = 'Bulk SMTP Test'
            msg.attach(MIMEText('Testing bulk SMTP sending...'))

            # Send test message
            smtp.send_message(msg)
            smtp.quit()

            # If we get here, SMTP is working
            assert True

        except Exception as e:
            pytest.fail(f"Bulk SMTP test failed: {str(e)}") 