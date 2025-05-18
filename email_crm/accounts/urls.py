from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # API routes
    path('register/', views.RegisterView.as_view(), name='register-api'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Auth routes
    path('login-jwt/', views.login_jwt, name='login-jwt'),
    
    # Template routes
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register-form/', views.register_view, name='register'),
    path('registration-success/<str:username>/', views.registration_success_view, name='registration_success'),
    path('profile-edit/', views.profile_view, name='profile-edit'),
] 