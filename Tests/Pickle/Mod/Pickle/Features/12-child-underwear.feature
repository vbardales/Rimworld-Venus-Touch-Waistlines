@review @child-underwear @timeout:180
Feature: child loincloth and trousers, from every facing

  Background:
    Given the save "Nelims-tribe" is loaded

  @requires:wdi.realistic.bodies @requires:Malistaticy.UnderWhere @requires:ab.vplrf @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: two children show whether trousers overlap WDI's loincloth
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "Loin-Boy" exists
    And "Loin-Boy" is 8 years old
    And "Loin-Boy" gender is male
    And Nelim's Pickle Tools: "Loin-Boy" body type is Child
    And a colonist "Loin-Girl" exists
    And "Loin-Girl" is 8 years old
    And "Loin-Girl" gender is female
    And Nelim's Pickle Tools: "Loin-Girl" body type is Child
    And Nelim's Pickle Tools: "Loin-Boy" stands at (198, 185) facing South
    And Nelim's Pickle Tools: "Loin-Girl" stands at (202, 185) facing South
    And I destroy the gear of "Loin-Boy"
    And Nelim's Pickle Tools: "Loin-Boy" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And I destroy the gear of "Loin-Girl"
    And Nelim's Pickle Tools: "Loin-Girl" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 90 ticks
    And Nelim's Pickle Tools: "Loin-Boy" faces South
    And Nelim's Pickle Tools: "Loin-Girl" faces South
    And I wait 2 ticks
    And I take a screenshot "child underwear, south, loincloth only"
    And Nelim's Pickle Tools: "Loin-Boy" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "Loin-Girl" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And I wait 90 ticks
    And I take a screenshot "child underwear, south, loincloth under trousers"
    And Nelim's Pickle Tools: "Loin-Boy" faces East
    And Nelim's Pickle Tools: "Loin-Girl" faces East
    And I wait 2 ticks
    And I take a screenshot "child underwear, east, loincloth under trousers"
    And Nelim's Pickle Tools: "Loin-Boy" faces North
    And Nelim's Pickle Tools: "Loin-Girl" faces North
    And I wait 2 ticks
    And I take a screenshot "child underwear, north, loincloth under trousers"
    Then no warning matching "Could not load UnityEngine.Texture2D" was logged
    And no warning matching "Failed to find any textures" was logged
