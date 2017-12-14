Feature: Annual report

  Scenario: Annual report is present
    Given file is an organisation file
     Then `document-link/category[@code="B01"]` should be present
