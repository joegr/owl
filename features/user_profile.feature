Feature: User Profile Management
  As a business user
  I want to manage my profile settings
  So that I can customize my CRM experience

  Background:
    Given I am logged in

  Scenario: User views profile settings
    Given I click on my profile icon
    When I select "Profile Settings"
    Then I should see my current profile information

  Scenario: User updates profile information
    Given I am on the profile settings page
    When I update my personal information
    And I click "Save Changes"
    Then I should see a success message
    And my profile should be updated

  Scenario: User changes password
    Given I am on the profile settings page
    When I navigate to the "Security" section
    And I enter my current password
    And I enter a new password
    And I confirm the new password
    And I click "Update Password"
    Then I should see a success message
    And my password should be updated 