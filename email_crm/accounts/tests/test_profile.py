import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Profile

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client():
    user = User.objects.create_user(
        username='profileuser',
        email='profile@example.com',
        password='profilepass123'
    )
    Profile.objects.create(user=user)
    
    client = APIClient()
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': 'profileuser', 'password': 'profilepass123'},
        format='json'
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    return client, user

@pytest.mark.django_db
class TestProfile:
    """Test cases for user profile management."""

    def test_view_profile(self, authenticated_client):
        """Test viewing user profile information."""
        client, user = authenticated_client
        
        response = client.get(reverse('accounts:profile'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id
        assert response.data['username'] == 'profileuser'
        assert response.data['email'] == 'profile@example.com'
        assert 'profile' in response.data

    def test_update_profile(self, authenticated_client):
        """Test updating user profile information."""
        client, user = authenticated_client
        
        # Update user and profile data
        response = client.put(
            reverse('accounts:profile'),
            {
                'first_name': 'Updated',
                'last_name': 'User',
                'profile': {
                    'company_name': 'Test Company',
                    'position': 'Manager',
                    'phone': '+1234567890'
                }
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check if user data was updated
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'User'
        
        # Check if profile data was updated
        profile = Profile.objects.get(user=user)
        assert profile.company_name == 'Test Company'
        assert profile.position == 'Manager'
        assert profile.phone == '+1234567890'

    def test_protected_profile_access(self, api_client):
        """Test that profile endpoint is protected."""
        response = api_client.get(reverse('accounts:profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 