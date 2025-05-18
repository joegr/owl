from django.db import models
from django.contrib.auth.models import User
from contacts.models import Contact

class EmailTemplate(models.Model):
    """Model representing an email template."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class SentEmail(models.Model):
    """Model representing a sent email."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_emails')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='received_emails')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    mailgun_id = models.CharField(max_length=100, blank=True, null=True)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.contact.name} - {self.subject}"
        
    @property
    def is_scheduled(self):
        """Return True if the email is scheduled for the future."""
        return self.scheduled_time is not None
