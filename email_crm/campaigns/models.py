from django.db import models
from django.conf import settings
from contacts.models import Contact
from emails.models import EmailTemplate

class Campaign(models.Model):
    """Model for email campaigns"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    from_name = models.CharField(max_length=100, blank=True)
    from_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        
    @property
    def open_rate(self):
        """Calculate email open rate as a percentage"""
        contacts = self.campaign_contacts.all().count()
        if contacts == 0:
            return 0
        opened = self.campaign_contacts.filter(opened=True).count()
        return (opened / contacts) * 100
    
    @property
    def click_rate(self):
        """Calculate email click rate as a percentage"""
        opened = self.campaign_contacts.filter(opened=True).count()
        if opened == 0:
            return 0
        clicked = self.campaign_contacts.filter(clicked=True).count()
        return (clicked / opened) * 100
        
    @property
    def status(self):
        """Return the status of the campaign"""
        if self.is_sent:
            return "sent"
        elif self.scheduled_at:
            return "scheduled"
        else:
            return "draft"

class CampaignContact(models.Model):
    """Model for tracking campaign recipients"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_contacts')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='campaign_contacts')
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking metrics
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    opened_count = models.IntegerField(default=0)
    
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    clicked_count = models.IntegerField(default=0)
    
    # Tracking click URLs
    clicked_urls = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.contact.name} in {self.campaign.name}"
    
    class Meta:
        unique_together = ('campaign', 'contact')
        ordering = ['-sent_at']

class CampaignList(models.Model):
    """Model for reusable contact lists that can be used for campaigns"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contact_lists')
    contacts = models.ManyToManyField(Contact, related_name='contact_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
