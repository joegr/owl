Feature: Bulk Email Sending
  As a business user
  I want to send emails to multiple contacts at once
  So that I can efficiently communicate with groups of customers

  Background:
    Given I am logged in
    And I have contacts in my list
    And I have email templates available

  Scenario: User sends a bulk email to multiple contacts
    Given I am on the contacts page
    When I select multiple contacts
    And I click the "Bulk Email" button
    And I select an email template
    And I click the "Send" button
    Then I should see a confirmation message
    And the emails should be queued for sending

  Scenario: User schedules a bulk email for later delivery
    Given I am on the contacts page
    When I select multiple contacts
    And I click the "Bulk Email" button
    And I select an email template
    And I set a future delivery date
    And I click the "Schedule" button
    Then I should see a confirmation message
    And the emails should be scheduled for the specified time 