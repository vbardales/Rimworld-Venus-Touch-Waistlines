# Shirts tucked into the trousers by default (Virginie, 2026-11-05). NSB's outfits for Nelim (WDI Female) showed
# Apparel_BasicShirt drawn down over the legs, hiding the trousers (tickets c585, 83b8). With the option on, its new
# default, the shirt is cut at the trousers waistband. Male and Female, front, side and back, in the frame of 26-nude-front:
# the basic shirt alone, then with the vanilla trousers. Pass: wsl-deps.shirt-tucked.map.
@review @shirt-tucked @timeout:600
Feature: the basic shirt tucked into the trousers on WDI's bodies

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:wdi.realistic.bodies @requires:ab.vplrf @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: the basic shirt, then the shirt with trousers, Male and Female (South, East, North)
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
    And Nelim's Pickle Tools: "M-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-South" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-East" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-North" wears "Apparel_BasicShirt"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "basic shirt alone"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "F-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "F-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "F-North" wears "Apparel_Pants"
    And I wait 120 ticks
    And I take a screenshot "basic shirt with trousers"
