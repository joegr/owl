Feature: CRM Dashboard
  As a business user
  I want to see a summary of my CRM activities
  So that I can quickly assess my customer engagement

  Background:
    Given I am logged in

  Scenario: User views dashboard
    Given I am on the dashboard page
    Then I should see summary information including:
      | Metric                | Type    |
      | Total Contacts        | Number  |
      | Emails Sent (Today)   | Number  |
      | Open Rate (Average)   | Percent |
      | Recent Activities     | List    |

  Scenario: User navigates to different sections from dashboard
    Given I am on the dashboard page
    When I click on a dashboard widget
    Then I should be taken to the corresponding detailed section

  Scenario: User customizes dashboard layout
    Given I am on the dashboard page
    When I click the "Customize" button
    And I rearrange the dashboard widgets
    And I save the changes
    Then I should see my customized dashboard layout 