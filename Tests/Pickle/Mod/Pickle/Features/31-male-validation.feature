# Validation test for Male (Virginie, 2026-11-06): the same man in three facings (South, East, North), eight states, all drawn
# with VTW active. Shirt from Vanilla Apparel Expanded (VAE_Apparel_CasualTShirt: closed hem, a texture per body type),
# shorts from Vanilla Apparel Expanded (VAE_Apparel_Shorts), trousers Apparel_Pants through AB, underwear UnderWhere boxers.
# State 5 needs the shirt worn over the trousers: config/male-validation lists VAE_Apparel_CasualTShirt in untuckedShirts,
# while Apparel_BasicShirt stays tucked (the default), so states 4 and 5 use two different shirts in the same launch.
# Pass: wsl-deps.male-validation.map.
@review @male-validation @timeout:900
Feature: Male on WDI's body, eight states, three facings

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:wdi.realistic.bodies @requires:ab.vplrf @requires:vanillaexpanded.vappe @requires:malistaticy.underwhere @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: Male, bare, shirts, trousers, underwear, shorts (South, East, North)
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-South" exists
    And "M-South" gender is male
    And Nelim's Pickle Tools: "M-South" body type is Male
    And Nelim's Pickle Tools: "M-South" stands at (197, 186) facing South
    And I draft "M-South"
    And a colonist "M-East" exists
    And "M-East" gender is male
    And Nelim's Pickle Tools: "M-East" body type is Male
    And Nelim's Pickle Tools: "M-East" stands at (200, 186) facing East
    And I draft "M-East"
    And a colonist "M-North" exists
    And "M-North" gender is male
    And Nelim's Pickle Tools: "M-North" body type is Male
    And Nelim's Pickle Tools: "M-North" stands at (203, 186) facing North
    And I draft "M-North"
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "1 bare WDI body"
    # 2 vanilla shirt
    And Nelim's Pickle Tools: "M-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_BasicShirt"
    And I wait 120 ticks
    And I take a screenshot "2 vanilla shirt"
    # 3 VAE shirt, no underwear
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Pickle Tools: "M-South" wears "VAE_Apparel_CasualTShirt"
    And Nelim's Pickle Tools: "M-East" wears "VAE_Apparel_CasualTShirt"
    And Nelim's Pickle Tools: "M-North" wears "VAE_Apparel_CasualTShirt"
    And I wait 120 ticks
    And I take a screenshot "3 VAE shirt, no underwear"
    # 4 shirt tucked into the trousers
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_Pants"
    And I wait 120 ticks
    And I take a screenshot "4 shirt tucked into the trousers"
    # 5 shirt over the trousers (VAE_Apparel_CasualTShirt is in untuckedShirts)
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Pickle Tools: "M-South" wears "VAE_Apparel_CasualTShirt"
    And Nelim's Pickle Tools: "M-East" wears "VAE_Apparel_CasualTShirt"
    And Nelim's Pickle Tools: "M-North" wears "VAE_Apparel_CasualTShirt"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_Pants"
    And I wait 120 ticks
    And I take a screenshot "5 shirt over the trousers"
    # 6 trousers alone
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_Pants"
    And I wait 120 ticks
    And I take a screenshot "6 trousers alone"
    # 7 trousers and underwear
    And Nelim's Pickle Tools: "M-South" wears "UnderWhere_Boxers"
    And Nelim's Pickle Tools: "M-East" wears "UnderWhere_Boxers"
    And Nelim's Pickle Tools: "M-North" wears "UnderWhere_Boxers"
    And I wait 120 ticks
    And I take a screenshot "7 trousers and underwear"
    # 8 shorts
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And Nelim's Pickle Tools: "M-South" wears "VAE_Apparel_Shorts"
    And Nelim's Pickle Tools: "M-East" wears "VAE_Apparel_Shorts"
    And Nelim's Pickle Tools: "M-North" wears "VAE_Apparel_Shorts"
    And I wait 120 ticks
    And I take a screenshot "8 shorts"
