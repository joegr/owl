Feature: Individual Email Sending
  As a business user
  I want to send personalized emails to individual contacts
  So that I can communicate effectively with my customers

  Background:
    Given I am logged in
    And I have contacts in my list
    And I have email templates available

  Scenario: User sends an email to a contact
    Given I am viewing a contact's details
    When I click the "Send Email" button
    And I select an email template
    And I click the "Send" button
    Then I should see a success message
    And the email should be recorded in the contact's activity history

  Scenario: User sends a customized email to a contact
    Given I am viewing a contact's details
    When I click the "Send Email" button
    And I select an email template
    And I customize the email content
    And I click the "Send" button
    Then I should see a success message
    And the customized email should be sent to the contact 