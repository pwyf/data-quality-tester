Feature: Procurement

  Scenario Outline: Tender is present
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not any of A01, A02 or G01
     And `transaction/aid-type/@code` is not any of A01 or A02
     Then `document-link/category[@code="A10"]` should be present

  Scenario Outline: Contract is present
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     And `default-aid-type/@code` is not any of A01, A02 or G01
     And `transaction/aid-type/@code` is not any of A01 or A02
     Then `document-link/category[@code="A06"] | document-link/category[@code="A11"]` should be present
