import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Profile

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestRegistration:
    """Test cases for user registration."""

    def test_user_registration_success(self, api_client):
        """Test successful user registration."""
        # Count initial users
        initial_user_count = User.objects.count()
        initial_profile_count = Profile.objects.count()
        
        # Register new user
        response = api_client.post(
            reverse('accounts:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'newpassword123',
                'password2': 'newpassword123',
                'first_name': 'New',
                'last_name': 'User'
            },
            format='json'
        )
        
        # Check if registration was successful
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check if a new user was created
        assert User.objects.count() == initial_user_count + 1
        
        # Check if a profile was created for the user
        assert Profile.objects.count() == initial_profile_count + 1
        
        # Check if the user has the correct information
        new_user = User.objects.get(username='newuser')
        assert new_user.email == 'newuser@example.com'
        assert new_user.first_name == 'New'
        assert new_user.last_name == 'User'

    def test_user_registration_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        # Register with mismatched passwords
        response = api_client.post(
            reverse('accounts:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'newpassword123',
                'password2': 'differentpassword',
                'first_name': 'New',
                'last_name': 'User'
            },
            format='json'
        )
        
        # Check if registration failed
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        
        # Check that no user was created
        assert not User.objects.filter(username='newuser').exists()

    def test_user_registration_duplicate_username(self, api_client):
        """Test registration fails with duplicate username."""
        # Create a user first
        User.objects.create_user(username='existinguser', email='existing@example.com', password='password123')
        
        # Try to register with the same username
        response = api_client.post(
            reverse('accounts:register'),
            {
                'username': 'existinguser',
                'email': 'new@example.com',
                'password': 'newpassword123',
                'password2': 'newpassword123',
                'first_name': 'New',
                'last_name': 'User'
            },
            format='json'
        )
        
        # Check if registration failed
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data 