"""
URL configuration for email_crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from contacts import views as contacts_views

urlpatterns = [
    # Homepage and admin
    path('', TemplateView.as_view(template_name='home/index.html'), name='home'),
    path('admin/', admin.site.urls),
    
    # App endpoints
    path('accounts/', include('accounts.urls')),
    path('contacts/', include('contacts.urls')),
    path('emails/', include('emails.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('campaigns/', include('campaigns.urls')),
    
    # API endpoints
    path('api/contacts/', contacts_views.ContactListCreateView.as_view(), name='api-contacts'),
    path('api/contacts/<int:pk>/', contacts_views.ContactDetailView.as_view(), name='api-contact-detail'),
    path('api/contacts/search/', contacts_views.ContactSearchView.as_view(), name='api-contact-search'),
    path('api/contacts/<int:contact_id>/emails/', contacts_views.contact_emails_view, name='api-contact-emails'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
