Feature: Finance type

  Scenario Outline: Default finance type
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then `default-finance-type | transaction/finance-type` should be present

  Scenario Outline: Finance type uses standard codelist
    Given the activity is current
     And `activity-status/@code` is one of 2, 3 or 4
     Then every `default-finance-type/@code | transaction/finance-type/@code` should be on the FinanceType codelist
