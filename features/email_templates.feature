Feature: Email Template Management
  As a business user
  I want to create and manage email templates
  So that I can maintain consistent communications

  Background:
    Given I am logged in

  Scenario: User creates an email template
    Given I am on the templates page
    When I click the "Create Template" button
    And I fill in the template details
    And I click the "Save" button
    Then I should see a success message
    And the template should appear in my templates list

  Scenario: User edits an email template
    Given I have templates in my list
    When I select a template to edit
    And I modify the template content
    And I save the changes
    Then I should see a success message
    And the template should be updated

  Scenario: User deletes an email template
    Given I have templates in my list
    When I select a template to delete
    And I confirm the deletion
    Then I should see a success message
    And the template should be removed from my list 