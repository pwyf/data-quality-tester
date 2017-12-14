Feature: Budget

  Scenario Outline: Budget available forward annually
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     And `activity-date[@type="3"]/@iso-date | activity-date[@type="4"]/@iso-date` is at least 6 months ahead
     Then `budget | planned-disbursement` should be available forward annually

  Scenario Outline: Budget available forward quarterly
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     And `activity-date[@type="3"]/@iso-date | activity-date[@type="4"]/@iso-date` is at least 6 months ahead
     Then `budget | planned-disbursement` should be available forward quarterly
