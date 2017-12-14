Feature: Impact appraisal

  Scenario Outline: Pre- and/or post-project impact appraisal documents
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not G01
     Then `document-link/category[@code="A01"]` should be present
