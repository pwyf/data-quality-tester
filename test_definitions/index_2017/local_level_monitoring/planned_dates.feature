Feature: Planned dates

  Scenario Outline: Planned start date is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then `activity-date[@type="1"]` should be present

  Scenario Outline: Planned end date is present
    Given the activity is current
     and `activity-status/@code` is one of 3 or 4
     then `activity-date[@type="3"]` should be present
