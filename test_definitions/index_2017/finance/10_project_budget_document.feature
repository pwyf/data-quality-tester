Feature: Budget document

  Scenario Outline: Budget document is present
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not any of A01, A02 or G01
     And `transaction/aid-type/@code` is not any of A01 or A02
     Then `document-link/category[@code="A05"]` should be present
