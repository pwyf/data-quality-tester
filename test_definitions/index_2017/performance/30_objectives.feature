Feature: Objectives

  Scenario Outline: Objectives of activity document
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     Then `document-link/category[@code="A02"] | description[@type="2"]` should be present
