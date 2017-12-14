Feature: Disbursements and expenditures

  Scenario Outline: Disbursements or expenditures are present
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `transaction/transaction-type[@code="3"] | transaction/transaction-type[@code="D"] | transaction/transaction-type[@code="4"] | transaction/transaction-type[@code="E"]` should be present
