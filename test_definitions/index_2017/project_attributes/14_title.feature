Feature: Title

  Scenario Outline: Title is present
    Given the activity is current
     Then `title/text() | title/narrative/text()` should be present

  Scenario Outline: Title has at least 10 characters
    Given the activity is current
     Then `title/text() | title/narrative/text()` should have at least 10 characters
