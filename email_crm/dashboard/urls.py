from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # API routes
    path('data/', views.DashboardView.as_view(), name='data'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('recent-activities/', views.RecentActivitiesView.as_view(), name='recent-activities'),
    
    # Template routes
    path('', views.dashboard_view, name='dashboard'),
] 