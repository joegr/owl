import hmac
import hashlib
import logging
import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import SentEmail

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def mailgun_webhook(request):
    """
    Webhook handler for Mailgun events.
    Handles "opened", "clicked", "delivered", "failed" events.
    """
    # Verify webhook signature
    signature = request.POST.get('signature', '')
    token = request.POST.get('token', '')
    timestamp = request.POST.get('timestamp', '')
    
    # Skip verification in debug mode
    if not settings.DEBUG:
        # Verify the webhook is from Mailgun
        hmac_digest = hmac.new(
            key=settings.MAILGUN_API_KEY.encode('utf-8'),
            msg='{}{}'.format(timestamp, token).encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if signature != hmac_digest:
            logger.warning('Invalid Mailgun webhook signature')
            return HttpResponse('Invalid signature', status=401)
    
    # Get event data
    event = request.POST.get('event')
    variables = request.POST.get('variables', '{}')
    
    try:
        variables_dict = json.loads(variables)
        tracking_id = variables_dict.get('tracking_id')
    except json.JSONDecodeError:
        tracking_id = None
        
    message_id = request.POST.get('message-id')
    
    logger.info(f'Received Mailgun webhook: {event} for message {message_id}, tracking ID: {tracking_id}')
    
    # Find the email by tracking ID or message ID
    email = None
    if tracking_id:
        email = SentEmail.objects.filter(tracking_id=tracking_id).first()
    
    if not email and message_id:
        email = SentEmail.objects.filter(mailgun_id=message_id).first()
    
    if not email:
        logger.warning(f'Could not find email for tracking ID {tracking_id} or message ID {message_id}')
        return HttpResponse('OK')
    
    # Process the event
    now = timezone.now()
    
    if event == 'opened':
        email.opened = True
        if not email.opened_at:
            email.opened_at = now
        email.open_count += 1
        logger.info(f'Email {email.id} opened by {email.contact.email}')
    
    elif event == 'clicked':
        email.clicked = True
        if not email.clicked_at:
            email.clicked_at = now
        email.click_count += 1
        logger.info(f'Email {email.id} clicked by {email.contact.email}')
    
    elif event == 'delivered':
        email.status = 'sent'
        logger.info(f'Email {email.id} delivered to {email.contact.email}')
    
    elif event == 'failed':
        email.status = 'failed'
        logger.info(f'Email {email.id} failed to deliver to {email.contact.email}')
    
    # Save the updated email
    email.save()
    
    return HttpResponse('OK') 