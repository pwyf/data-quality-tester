Feature: Planned dates

  Scenario Outline: Planned start date is present
    Given the activity is current
     then `activity-date[@type="1"]` should be present

  Scenario Outline: Planned end date is present
    Given the activity is current
     then `activity-date[@type="3"]` should be present
