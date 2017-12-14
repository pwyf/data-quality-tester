Feature: Conditions

  Scenario Outline: Conditions data
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `conditions` should be present

  Scenario Outline: Conditions document
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `document-link/category[@code="A04"]` should be present
