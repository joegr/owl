Feature: User Authentication
  As a business user
  I want to securely access the CRM system
  So that I can manage my customer relationships

  Scenario: User logs in
    Given I am on the login page
    When I enter valid credentials
    Then I should be redirected to the dashboard

  Scenario: User logs out
    Given I am logged in
    When I click the logout button
    Then I should be redirected to the login page

  Scenario: User attempts login with invalid credentials
    Given I am on the login page
    When I enter invalid credentials
    Then I should see an error message
    And I should remain on the login page 