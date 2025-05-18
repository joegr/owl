from django import forms
from .models import Campaign, CampaignList
from emails.models import EmailTemplate
from contacts.models import Contact
from django.conf import settings

class CampaignForm(forms.ModelForm):
    from_name = forms.CharField(max_length=100, required=True)
    from_email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=255, required=True)
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control rich-text-editor'}), required=True)
    
    class Meta:
        model = Campaign
        fields = ['name', 'description', 'from_name', 'from_email', 'subject', 'content', 'email_template', 'scheduled_at']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter email templates by user
        self.fields['email_template'].queryset = EmailTemplate.objects.filter(user=user)
        self.fields['email_template'].required = False
        
        # Initialize from_name and from_email with defaults
        if not self.initial.get('from_name'):
            self.initial['from_name'] = user.get_full_name() or user.username
        if not self.initial.get('from_email'):
            self.initial['from_email'] = user.email or settings.DEFAULT_FROM_EMAIL
            
        # Add contact list field for recipient selection
        self.fields['contact_list'] = forms.ModelChoiceField(
            queryset=CampaignList.objects.filter(user=user),
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Add fields for contact filtering
        companies = Contact.objects.filter(user=user).values_list('company', flat=True).distinct()
        companies = [c for c in companies if c]
        self.fields['companies'] = forms.MultipleChoiceField(
            choices=[(company, company) for company in companies],
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-select'})
        )
        
        positions = Contact.objects.filter(user=user).values_list('position', flat=True).distinct()
        positions = [p for p in positions if p]
        self.fields['positions'] = forms.MultipleChoiceField(
            choices=[(position, position) for position in positions],
            required=False,
            widget=forms.SelectMultiple(attrs={'class': 'form-select'})
        )

class CampaignListForm(forms.ModelForm):
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = CampaignList
        fields = ['name', 'description', 'contacts']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter contacts by user
        self.fields['contacts'].queryset = Contact.objects.filter(user=user)

class BulkEmailForm(forms.Form):
    subject = forms.CharField(max_length=255)
    body = forms.CharField(widget=forms.Textarea)
    email_template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.none(),
        required=False
    )
    save_as_template = forms.BooleanField(required=False)
    template_name = forms.CharField(max_length=255, required=False)
    create_campaign = forms.BooleanField(required=False)
    campaign_name = forms.CharField(max_length=255, required=False)
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter email templates by user
        self.fields['email_template'].queryset = EmailTemplate.objects.filter(user=user)
        
    def clean(self):
        cleaned_data = super().clean()
        save_as_template = cleaned_data.get('save_as_template')
        template_name = cleaned_data.get('template_name')
        create_campaign = cleaned_data.get('create_campaign')
        campaign_name = cleaned_data.get('campaign_name')
        
        if save_as_template and not template_name:
            self.add_error('template_name', 'Please provide a name for the template.')
            
        if create_campaign and not campaign_name:
            self.add_error('campaign_name', 'Please provide a name for the campaign.')
            
        return cleaned_data 