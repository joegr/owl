from django.contrib import admin
from .models import EmailTemplate, SentEmail

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'user', 'created_at')
    search_fields = ('name', 'subject', 'body')
    list_filter = ('created_at', 'user')

@admin.register(SentEmail)
class SentEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'contact', 'user', 'sent_at', 'opened')
    search_fields = ('subject', 'body')
    list_filter = ('sent_at', 'opened', 'clicked', 'user')
