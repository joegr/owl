Feature: Email Analytics
  As a business user
  I want to track the performance of my emails
  So that I can improve my communication strategy

  Background:
    Given I am logged in
    And I have sent emails to contacts

  Scenario: User views email analytics dashboard
    Given I navigate to the analytics page
    Then I should see summary statistics for my emails
    And I should see open rates and click rates

  Scenario: User views detailed analytics for a specific email
    Given I navigate to the analytics page
    When I select a specific email campaign
    Then I should see detailed metrics for that email
    And I should see a list of recipients who opened the email

  Scenario: User exports analytics data
    Given I am on the analytics page
    When I click the "Export Data" button
    And I select an export format
    Then the analytics data should be downloaded in the selected format 