Feature: Capital spend

  Scenario Outline: Capital spend is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not A01
     and `default-aid-type/@code` is not A02
     and `transaction/aid-type/@code` is not A01
     and `transaction/aid-type/@code` is not A02
     and `default-aid-type/@code` is not G01
     then `capital-spend` should be present
