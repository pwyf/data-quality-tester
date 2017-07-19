Feature: Disbursements and expenditures

  Scenario Outline: Disbursements or expenditures are present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either `transaction/transaction-type[@code="3"]` or `transaction/transaction-type[@code="4"]` should be present
