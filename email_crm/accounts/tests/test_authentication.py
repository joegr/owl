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
    """Test cases for the authentication feature."""
    
    def test_login_with_valid_credentials_api(self, api_client):
        """
        Feature: User Authentication
        Scenario: User logs in
        Given I am on the login page
        When I enter valid credentials
        Then I should be redirected to the dashboard
        
        Tests the API-based login flow with session authentication.
        """
        # Create a user
        User.objects.create_user(username='testuser', password='testpassword123')
        
        # Attempt to login via API (using session auth)
        response = api_client.post(
            reverse('accounts:login-jwt'),
            {'username': 'testuser', 'password': 'testpassword123'}
        )
        
        # Check for redirection which indicates a successful login
        assert response.status_code == 302
        
        # Verify the client is authenticated
        assert '_auth_user_id' in api_client.session
        
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
        User.objects.create_user(username='testuser', password='testpassword123')
        
        # Attempt to login through the form (using the correct login URL)
        response = django_client.post(
            reverse('accounts:login-jwt'),
            {'username': 'testuser', 'password': 'testpassword123', 'next': '/dashboard/'},
            follow=True
        )
        
        # Check if user is redirected to dashboard after login
        assert response.status_code == 200
        assert any(redirect[0].endswith('/dashboard/') for redirect in response.redirect_chain)
        
        # Verify the client is authenticated
        assert '_auth_user_id' in django_client.session
        
    def test_logout(self, api_client, test_user):
        """
        Feature: User Authentication
        Scenario: User logs out
        Given I am logged in
        When I click the logout button
        Then I should be redirected to the login page
        """
        # Login first
        api_client.force_login(test_user)
        
        # Verify the client is authenticated
        assert '_auth_user_id' in api_client.session
        
        # Logout
        response = api_client.get(reverse('accounts:logout'), follow=True)
        
        # Check redirection to login page
        assert response.status_code == 200
        assert any('/accounts/login/' in redirect[0] for redirect in response.redirect_chain)
        
        # Verify the client is no longer authenticated
        assert '_auth_user_id' not in api_client.session
        
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
        
        # Verify redirection to login page
        assert '/accounts/login/' in [redirect[0] for redirect in response.redirect_chain]
        
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
            reverse('accounts:login-jwt'),
            {'username': 'testuser', 'password': 'wrongpassword'},
            follow=True
        )
        
        # Check user remains on the login page
        assert reverse('accounts:login') in str(response.content)
        
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
        User.objects.create_user(username='testuser', password='testpassword123')
        
        # Attempt to login with wrong password
        response = django_client.post(
            reverse('accounts:login'),
            {'username': 'testuser', 'password': 'wrongpassword'},
            follow=True
        )
        
        # Check if user stays on the login page
        assert reverse('accounts:login') in str(response.content) 