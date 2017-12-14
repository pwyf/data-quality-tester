Feature: Current status

  Scenario Outline: Current status is present
    Given the activity is current
     Then `activity-status` should be present

  Scenario Outline: Current status is valid
    Given the activity is current
     Then every `activity-status/@code` should be on the ActivityStatus codelist
