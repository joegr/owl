import logging
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from emails.models import SentEmail
from dashboard.models import Activity
from emails.utils import EmailTemplateProcessor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send scheduled emails that are due to be sent'
    
    def handle(self, *args, **options):
        self.stdout.write('Checking for scheduled emails to send...')
        
        # Get all emails that are scheduled and due to be sent
        now = timezone.now()
        scheduled_emails = SentEmail.objects.filter(
            scheduled_time__lte=now,  # scheduled time is in the past or now
            status='pending'           # still pending to be sent
        )
        
        self.stdout.write(f'Found {scheduled_emails.count()} scheduled emails to send')
        
        sent_count = 0
        error_count = 0
        
        for email in scheduled_emails:
            try:
                # Send email with Django's EmailMessage
                from django.core.mail import EmailMessage
                message = EmailMessage(
                    subject=email.subject,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email.contact.email],
                )
                
                # Set the body
                message.body = email.body
                
                # Use the existing tracking ID or create a new one
                if not email.tracking_id:
                    import uuid
                    email.tracking_id = str(uuid.uuid4())
                
                # Prepare message headers for tracking
                message.extra_headers = {
                    'X-Mailgun-Track': 'yes',
                    'X-Mailgun-Track-Clicks': 'yes',
                    'X-Mailgun-Track-Opens': 'yes',
                    'X-Mailgun-Variables': json.dumps({'tracking_id': email.tracking_id}),
                }
                
                # Send the message
                message_id = message.send()
                
                # Update the sent email
                email.mailgun_id = message_id
                email.status = 'sent'
                email.save()
                
                # Record activity
                Activity.objects.create(
                    user=email.user,
                    activity_type='email_sent',
                    description=f'Sent scheduled email to {email.contact.name}: {email.subject}',
                    content_object=email
                )
                
                sent_count += 1
                self.stdout.write(f'Sent email to {email.contact.email}')
                
            except Exception as e:
                error_count += 1
                logger.error(f'Error sending scheduled email {email.id}: {str(e)}')
                email.status = 'failed'
                email.save()
                
        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {scheduled_emails.count()} scheduled emails: '
            f'{sent_count} sent, {error_count} errors'
        )) 