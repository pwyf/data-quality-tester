Feature: Budget alignment

  Scenario Outline: Budget alignment
    Given at least one `sector[@vocabulary="DAC"]/@code | sector[not(@vocabulary)]/@code | sector[@vocabulary="1"]/@code | transaction/sector[@vocabulary="1"]/@code | transaction/sector[not(@vocabulary)]/@code` is on the Sector codelist
     then every `sector[@vocabulary="DAC"]/@code | sector[not(@vocabulary)]/@code | sector[@vocabulary="1"]/@code | transaction/sector[@vocabulary="1"]/@code | transaction/sector[not(@vocabulary)]/@code` should be on the BudgetAlignment codelist
