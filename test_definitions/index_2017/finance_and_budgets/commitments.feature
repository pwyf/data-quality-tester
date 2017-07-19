Feature: Commitments

  Scenario Outline: Commitment is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then `transaction/transaction-type[@code="2"]` should be present
