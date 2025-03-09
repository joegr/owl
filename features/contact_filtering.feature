Feature: Contact Filtering and Search
  As a business user
  I want to filter and search my contacts
  So that I can find specific customers quickly

  Background:
    Given I am logged in
    And I have multiple contacts in my list

  Scenario: User filters contacts by criteria
    Given I am on the contacts page
    When I apply filters based on specific criteria
    Then I should see only the contacts that match my filter criteria

  Scenario: User searches for a contact
    Given I am on the contacts page
    When I enter a search term in the search box
    Then I should see contacts that match my search term

  Scenario: User saves a filter for future use
    Given I am on the contacts page
    When I apply filters based on specific criteria
    And I click "Save Filter"
    And I provide a name for the filter
    Then I should be able to access this saved filter in the future 