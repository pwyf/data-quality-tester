Feature: Reviews and evaluations

  Scenario Outline: Project performance and evaluation document
    Given the activity is current
     And `activity-status/@code` is one of 3 or 4
     And `default-aid-type/@code` is not G01
     Then `document-link/category[@code="A07"]` should be present
