Feature: Tied aid status

  Scenario Outline: Tied aid status
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `default-tied-status | transaction/tied-status` should be present

  Scenario Outline: Tied aid status uses standard codelist
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then every `default-tied-status/@code | transaction/tied-status/@code` should be on the TiedStatus codelist
