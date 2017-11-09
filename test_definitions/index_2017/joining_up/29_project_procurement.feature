Feature: Procurement

  Scenario Outline: Tender is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not A01
     and `default-aid-type/@code` is not A02
     and `transaction/aid-type/@code` is not A01
     and `transaction/aid-type/@code` is not A02
     and `default-aid-type/@code` is not G01
     then `document-link/category[@code="A10"]` should be present

  Scenario Outline: Contract is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not A01
     and `default-aid-type/@code` is not A02
     and `transaction/aid-type/@code` is not A01
     and `transaction/aid-type/@code` is not A02
     and `default-aid-type/@code` is not G01
     then either `document-link/category[@code="A06"]` or `document-link/category[@code="A11"]` should be present
