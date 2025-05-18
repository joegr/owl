from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.campaign_list, name='list'),
    path('create/', views.campaign_create, name='create'),
    path('<int:campaign_id>/', views.campaign_detail, name='detail'),
    path('<int:campaign_id>/edit/', views.campaign_edit, name='edit'),
    path('<int:campaign_id>/delete/', views.campaign_delete, name='delete'),
    
    # Contact lists
    path('lists/', views.list_list, name='list_list'),
    path('lists/create/', views.list_create, name='list_create'),
    path('lists/<int:list_id>/', views.list_detail, name='list_detail'),
    path('lists/<int:list_id>/edit/', views.list_edit, name='list_edit'),
    path('lists/<int:list_id>/delete/', views.list_delete, name='list_delete'),
    
    # API endpoints
    path('api/', views.CampaignListAPIView.as_view(), name='api-list'),
    path('api/<int:campaign_id>/', views.CampaignDetailAPIView.as_view(), name='api-detail'),
    path('api/recent/', views.RecentCampaignsAPIView.as_view(), name='api-recent'),
    path('api/list-contacts/', views.ListContactsAPIView.as_view(), name='api-list-contacts'),
    path('api/filter-contacts/', views.FilterContactsAPIView.as_view(), name='api-filter-contacts'),
] 