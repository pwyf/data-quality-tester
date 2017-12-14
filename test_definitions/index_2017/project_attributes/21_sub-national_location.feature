Feature: Sub-national location

  Scenario Outline: Location (sub-national)
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `recipient-region/@code` is not 998
     And `sector/@code` is not 91010
     Then `location` should be present

  Scenario Outline: Location (sub-national) coordinates or point
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `recipient-region/@code` is not 998
     Then `location/coordinates | location/point` should be present
