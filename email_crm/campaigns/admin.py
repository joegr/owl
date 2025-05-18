from django.contrib import admin
from .models import Campaign, CampaignContact, CampaignList

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_sent', 'sent_at', 'created_at')
    list_filter = ('is_sent', 'created_at', 'user')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(CampaignContact)
class CampaignContactAdmin(admin.ModelAdmin):
    list_display = ('contact', 'campaign', 'is_sent', 'opened', 'clicked')
    list_filter = ('is_sent', 'opened', 'clicked', 'campaign')
    search_fields = ('contact__name', 'contact__email', 'campaign__name')

@admin.register(CampaignList)
class CampaignListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'description')
    filter_horizontal = ('contacts',)
