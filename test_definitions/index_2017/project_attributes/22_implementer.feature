Feature: Implementer

  Scenario Outline: Implementing organisation
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `participating-org[@role="Implementing"] | participating-org[@role="4"]` should be present
