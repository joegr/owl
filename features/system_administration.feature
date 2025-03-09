Feature: System Administration
  As an administrator
  I want to manage system settings and users
  So that I can maintain the CRM system effectively

  Background:
    Given I am logged in as an administrator

  Scenario: Admin adds a new user
    Given I am on the admin dashboard
    When I navigate to "User Management"
    And I click "Add User"
    And I fill in the user details
    And I click "Create User"
    Then I should see a success message
    And the new user should appear in the user list

  Scenario: Admin modifies user permissions
    Given I am on the admin dashboard
    When I navigate to "User Management"
    And I select a user from the list
    And I modify their role and permissions
    And I click "Save Changes"
    Then I should see a success message
    And the user's permissions should be updated

  Scenario: Admin configures email settings
    Given I am on the admin dashboard
    When I navigate to "System Settings"
    And I update the email configuration settings
    And I click "Save Settings"
    Then I should see a success message
    And the new email settings should be applied 