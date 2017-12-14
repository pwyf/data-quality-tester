Feature: Commitment

  Scenario Outline: Commitment is present
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `transaction/transaction-type[@code="2"] | transaction/transaction-type[@code="C"]` should be present
