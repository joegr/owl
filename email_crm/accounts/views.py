from django.shortcuts import render, redirect
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from .models import Profile
from .serializers import UserSerializer, ProfileSerializer, RegisterSerializer
from django.views.decorators.http import require_http_methods
import json
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    """API view for user registration."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        """Override to add custom validation and error handling."""
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = request.data
            else:
                data = request.POST.dict()
            
            # Log request data for debugging
            logger.info(f"Registration request received: {data}")
            
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                logger.warning(f"Registration validation errors: {serializer.errors}")
                
                # If it's a form submission, add message and redirect
                if request.content_type != 'application/json':
                    for field, errors in serializer.errors.items():
                        error_msg = f"{field}: {' '.join(str(e) for e in errors)}"
                        messages.error(request, error_msg)
                    return redirect('accounts:register')
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            # Log success
            logger.info(f"User registered successfully: {user.username}")
            
            # Create profile for the user
            Profile.objects.get_or_create(user=user)
            
            # If it's a form submission, redirect to the success page
            if request.content_type != 'application/json':
                # Add a flash message
                messages.success(request, f"Account created successfully for {user.username}! You can now log in.")
                logger.info(f"Redirecting to registration success page")
                
                # Redirect to success page with username
                return redirect('accounts:registration_success', username=user.username)
            
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            
            # If it's a form submission, add message and redirect
            if request.content_type != 'application/json':
                messages.error(request, f"Registration failed: {str(e)}")
                return redirect('accounts:register')
            
            return Response(
                {"error": "An unexpected error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get the current user's profile information."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user and profile information."""
        user = request.user
        user_data = request.data
        profile_data = user_data.pop('profile', {})
        
        # Update user data
        user_serializer = UserSerializer(user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            
            # Update profile data if it exists
            if profile_data:
                profile, created = Profile.objects.get_or_create(user=user)
                profile_serializer = ProfileSerializer(profile, data=profile_data, partial=True)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                else:
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Return updated user with profile
            return Response(UserSerializer(user).data)
        
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Form-based login with Django session authentication
@require_http_methods(["POST"])
def login_jwt(request):
    """Handle form-based login using Django's session authentication."""
    username = request.POST.get('username')
    password = request.POST.get('password')
    next_url = request.POST.get('next', '/dashboard/')
    
    # Log login attempt for debugging
    logger.info(f"Login attempt for user: {username}")
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        # Use Django's login function to create a session
        login(request, user)
        
        # Log successful login
        logger.info(f"Login successful for user: {username}")
        
        # Add success message
        messages.success(request, f"Welcome back, {user.username}!")
        
        return redirect(next_url)
    else:
        # Log failed login
        logger.warning(f"Login failed for user: {username}")
        
        messages.error(request, "Invalid username or password. Please try again.")
        return redirect('accounts:login')

# Template Views
def login_view(request):
    """Render the login page template."""
    return render(request, 'accounts/login.html')

def register_view(request):
    """Render the registration page template."""
    return render(request, 'accounts/register.html')

def registration_success_view(request, username):
    """Render the registration success page."""
    return render(request, 'accounts/registration_success.html', {'username': username})

@login_required
def profile_view(request):
    """Render the user profile page template."""
    return render(request, 'accounts/profile.html')

@login_required
def logout_view(request):
    """Handle user logout."""
    # Use Django's built-in logout functionality
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('accounts:login')
