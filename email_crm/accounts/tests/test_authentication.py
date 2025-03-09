import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.test import Client

"""
Tests for the authentication feature.
These tests cover the scenarios described in features/authentication.feature
"""

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def django_client():
    return Client()

@pytest.fixture
def test_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    return user

@pytest.mark.django_db
class TestAuthentication:
    """Test cases for the user authentication feature.
    Corresponds to features/authentication.feature
    """

    def test_login_with_valid_credentials_api(self, api_client):
        """
        Feature: User Authentication
        Scenario: User logs in
        Given I am on the login page
        When I enter valid credentials
        Then I should be redirected to the dashboard
        
        Tests the API-based login flow with JWT token.
        """
        # Create a user
        User.objects.create_user(username='testuser', password='testpassword123')
        
        # Attempt to login via API
        response = api_client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpassword123'},
            format='json'
        )
        
        # Check if login was successful
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_with_valid_credentials_form(self, django_client):
        """
        Feature: User Authentication
        Scenario: User logs in
        Given I am on the login page
        When I enter valid credentials
        Then I should be redirected to the dashboard
        
        Tests the form-based login flow.
        """
        # Create a user
        User.objects.create_user(username='formuser', password='testpassword123')
        
        # Attempt to login via form POST
        response = django_client.post(
            reverse('accounts:login-jwt'),
            {'username': 'formuser', 'password': 'testpassword123', 'next': '/dashboard/'},
            follow=True
        )
        
        # Check if login was successful and redirected to dashboard
        assert response.status_code == 200
        assert '/dashboard/' in [redirect[0] for redirect in response.redirect_chain]

    def test_logout(self, api_client, test_user):
        """
        Feature: User Authentication
        Scenario: User logs out
        Given I am logged in
        When I click the logout button
        Then I should be redirected to the login page
        
        Note: In JWT, logout is handled client-side by removing the token
        This test verifies that protected endpoints can't be accessed after logout
        """
        # Login first
        response = api_client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpassword123'},
            format='json'
        )
        token = response.data['access']
        
        # Set the token in the header
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Verify access to a protected endpoint
        response = api_client.get(reverse('accounts:profile'))
        assert response.status_code == status.HTTP_200_OK
        
        # "Logout" - clear credentials
        api_client.credentials()
        
        # Try accessing the same protected endpoint
        response = api_client.get(reverse('accounts:profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_form_logout(self, django_client, test_user):
        """
        Feature: User Authentication
        Scenario: User logs out
        Given I am logged in
        When I click the logout button
        Then I should be redirected to the login page
        
        Tests the form-based logout flow.
        """
        # Login first
        django_client.login(username='testuser', password='testpassword123')
        
        # Visit a protected page to confirm login
        response = django_client.get(reverse('dashboard:dashboard'))
        assert response.status_code == 200
        
        # Logout
        response = django_client.get(reverse('accounts:logout'), follow=True)
        
        # Verify redirection to home page
        assert '/' in [redirect[0] for redirect in response.redirect_chain]
        
        # Try accessing a protected page
        response = django_client.get(reverse('dashboard:dashboard'))
        assert '/accounts/login/' in response.url  # Redirected to login

    def test_login_with_invalid_credentials(self, api_client):
        """
        Feature: User Authentication
        Scenario: User attempts login with invalid credentials
        Given I am on the login page
        When I enter invalid credentials
        Then I should see an error message
        And I should remain on the login page
        
        Tests the API-based login flow with invalid credentials.
        """
        # Create a user
        User.objects.create_user(username='testuser', password='testpassword123')
        
        # Attempt to login with wrong password
        response = api_client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'wrongpassword'},
            format='json'
        )
        
        # Check if login failed as expected
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data

    def test_login_with_invalid_credentials_form(self, django_client):
        """
        Feature: User Authentication
        Scenario: User attempts login with invalid credentials
        Given I am on the login page
        When I enter invalid credentials
        Then I should see an error message
        And I should remain on the login page
        
        Tests the form-based login flow with invalid credentials.
        """
        # Create a user
        User.objects.create_user(username='formuser', password='testpassword123')
        
        # Attempt to login with wrong password
        response = django_client.post(
            reverse('accounts:login-jwt'),
            {'username': 'formuser', 'password': 'wrongpassword'},
            follow=True
        )
        
        # Check if we're redirected back to login page
        assert response.status_code == 200
        assert '/accounts/login/' in [redirect[0] for redirect in response.redirect_chain]
        
        # Check for messages
        messages = list(response.context.get('messages', []))
        assert any('Invalid username or password' in str(message) for message in messages) 