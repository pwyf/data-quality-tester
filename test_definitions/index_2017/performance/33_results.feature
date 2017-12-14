Feature: Results

  Scenario Outline: Results data
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     Then `result` should be present

  Scenario Outline: Results document
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     Then `document-link/category[@code="A08"]` should be present
