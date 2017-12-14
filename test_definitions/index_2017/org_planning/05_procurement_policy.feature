Feature: Procurement policy

  Scenario: Procurement policy is present
    Given file is an organisation file
     Then `document-link/category[@code="B05"]` should be present
