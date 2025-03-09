from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.ContactListCreateView.as_view(), name='contact-list'),
    path('<int:pk>/', views.ContactDetailView.as_view(), name='contact-detail'),
    path('search/', views.ContactSearchView.as_view(), name='contact-search'),
] 