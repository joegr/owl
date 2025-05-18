from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    # API routes
    path('', views.ContactListCreateView.as_view(), name='contact-list'),
    path('<int:pk>/', views.ContactDetailView.as_view(), name='contact-detail'),
    path('search/', views.ContactSearchView.as_view(), name='contact-search'),
    path('<int:contact_id>/emails/', views.contact_emails_view, name='contact-emails'),
    
    # Template routes
    path('list/', views.contact_list_view, name='list'),
    path('add/', views.contact_add_view, name='add'),
    path('view/<int:contact_id>/', views.contact_detail_view, name='view'),
    path('edit/<int:contact_id>/', views.contact_edit_view, name='edit'),
    path('delete/<int:contact_id>/', views.contact_delete_view, name='delete'),
] 