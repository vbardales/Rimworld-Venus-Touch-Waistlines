# LTS_Sweatpants (Raiments, limetreesnake.raiments) drew nothing: Raiments ships no worn graphic for them and AB's
# Normal_Pants keyword "Pants" is case-sensitive (NPT ticket dd05, 2026-11-04). Fix 2026-11-05: AB's config gets a lowercase
# "pants" keyword (config/sweatpants seeds it), and Venus treats every def on AB's trousers path as trousers, whatever its name.
# Same frame and bodies as 29-shirt-tucked: the sweatpants alone, then the basic shirt tucked into them. Pass: wsl-deps.sweatpants.map.
@review @sweatpants @timeout:600
Feature: LTS sweatpants drawn as trousers on WDI's bodies

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:ab.vplrf @requires:limetreesnake.raiments
  Scenario: AB gives the sweatpants the trousers path through the lowercase keyword
    Then def "LTS_Sweatpants" field "apparel.wornGraphicPath" is "Things/Pawn/Humanlike/Apparel/Pants/Pants"

  @requires:wdi.realistic.bodies @requires:ab.vplrf @requires:limetreesnake.raiments @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: the sweatpants, then the basic shirt tucked into them, Male and Female (South, East, North)
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
    And a colonist "F-South" exists
    And "F-South" gender is female
    And Nelim's Pickle Tools: "F-South" body type is Female
    And Nelim's Pickle Tools: "F-South" stands at (197, 184) facing South
    And I draft "F-South"
    And a colonist "F-East" exists
    And "F-East" gender is female
    And Nelim's Pickle Tools: "F-East" body type is Female
    And Nelim's Pickle Tools: "F-East" stands at (200, 184) facing East
    And I draft "F-East"
    And a colonist "F-North" exists
    And "F-North" gender is female
    And Nelim's Pickle Tools: "F-North" body type is Female
    And Nelim's Pickle Tools: "F-North" stands at (203, 184) facing North
    And I draft "F-North"
    And I destroy the gear of "M-South"
    And I destroy the gear of "M-East"
    And I destroy the gear of "M-North"
    And I destroy the gear of "F-South"
    And I destroy the gear of "F-East"
    And I destroy the gear of "F-North"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And Nelim's Pickle Tools: "M-South" wears "LTS_Sweatpants"
    And Nelim's Pickle Tools: "M-East" wears "LTS_Sweatpants"
    And Nelim's Pickle Tools: "M-North" wears "LTS_Sweatpants"
    And Nelim's Pickle Tools: "F-South" wears "LTS_Sweatpants"
    And Nelim's Pickle Tools: "F-East" wears "LTS_Sweatpants"
    And Nelim's Pickle Tools: "F-North" wears "LTS_Sweatpants"
    And I wait 120 ticks
    And I take a screenshot "sweatpants alone"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-North" wears "Apparel_BasicShirt"
    And I wait 120 ticks
    And I take a screenshot "basic shirt tucked into the sweatpants"
