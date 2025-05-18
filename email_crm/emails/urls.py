from django.urls import path
from . import views
from . import webhooks

app_name = 'emails'

urlpatterns = [
    # API routes
    path('templates/', views.EmailTemplateListCreateView.as_view(), name='template-list'),
    path('templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='template-detail'),
    path('send/<int:contact_id>/', views.SendEmailView.as_view(), name='send-email'),
    path('bulk-send/', views.BulkSendEmailView.as_view(), name='bulk-send-email'),
    path('analytics/', views.EmailAnalyticsView.as_view(), name='email-analytics'),
    path('analytics/export/', views.ExportAnalyticsView.as_view(), name='export-analytics'),
    path('analytics-dashboard/', views.email_analytics_dashboard_view, name='analytics_dashboard'),
    
    # Template routes for the email sending process
    path('select-contact/', views.select_contact_view, name='select_contact'),
    path('compose/<int:contact_id>/', views.compose_email_view, name='compose_email'),
    path('bulk-compose/', views.bulk_compose_email_view, name='bulk_compose'),
    path('preview/<int:contact_id>/', views.preview_email_view, name='preview_email'),
    path('send-confirmed/<int:contact_id>/', views.send_email_view, name='send_email'),
    path('bulk-send-confirmed/', views.bulk_send_email_view, name='bulk_send_email'),
    
    # Webhook routes
    path('webhooks/mailgun/', webhooks.mailgun_webhook, name='mailgun_webhook'),
] 