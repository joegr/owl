Feature: Contact Management
  As a business user
  I want to manage my contacts
  So that I can keep track of my customers

  Background:
    Given I am logged in

  Scenario: User adds a new contact
    Given I am on the contacts page
    When I click the "Add Contact" button
    And I fill in the contact details
    And I click the "Save" button
    Then I should see a success message
    And the contact should appear in my contact list

  Scenario: User views contact details
    Given I have contacts in my list
    When I click on a contact name
    Then I should see the contact's details

  Scenario: User edits a contact
    Given I am viewing a contact's details
    When I click the "Edit" button
    And I modify the contact's details
    And I click the "Save" button
    Then I should see a success message
    And the contact should display the updated information

  Scenario: User deletes a contact
    Given I am viewing a contact's details
    When I click the "Delete" button
    And I confirm the deletion
    Then I should see a success message
    And the contact should no longer appear in my list 