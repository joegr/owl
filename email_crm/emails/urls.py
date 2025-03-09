from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    path('templates/', views.EmailTemplateListCreateView.as_view(), name='template-list'),
    path('templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='template-detail'),
    path('send/<int:contact_id>/', views.SendEmailView.as_view(), name='send-email'),
    path('bulk-send/', views.BulkSendEmailView.as_view(), name='bulk-send-email'),
    path('analytics/', views.EmailAnalyticsView.as_view(), name='email-analytics'),
] 