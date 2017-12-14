Feature: Allocation policy

  Scenario: Allocation policy is present
    Given file is an organisation file
     Then `document-link/category[@code="B04"]` should be present
