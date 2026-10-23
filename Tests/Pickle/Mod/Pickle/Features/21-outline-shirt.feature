# The basic shirt drawn by Venus alone (no APP, no TailorMade, no AB): red outline of 5 px, interior empty, over UnderWhere underwear,
# on the ten WDI profiles, facing South (Virginie, 2026-10-23). Pass: wsl-deps.wdi-outline.map. Derived from 19-vanilla-wardrobe.
@review @outline-shirt @timeout:900
Feature: the basic shirt as an outline on every WDI silhouette

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:wdi.realistic.bodies @requires:LoneKin.ChildrenWearAnything @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: the basic shirt drawn as an outline on ten WDI silhouettes, facing South
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-Thin" exists
    And "M-Thin" gender is male
    And Nelim's Pickle Tools: "M-Thin" body type is Thin
    And Nelim's Pickle Tools: "M-Thin" stands at (196, 186) facing South
    And I draft "M-Thin"
    And a colonist "M-Avg" exists
    And "M-Avg" gender is male
    And Nelim's Pickle Tools: "M-Avg" body type is Male
    And Nelim's Pickle Tools: "M-Avg" stands at (198, 186) facing South
    And I draft "M-Avg"
    And a colonist "M-Fat" exists
    And "M-Fat" gender is male
    And Nelim's Pickle Tools: "M-Fat" body type is Fat
    And Nelim's Pickle Tools: "M-Fat" stands at (200, 186) facing South
    And I draft "M-Fat"
    And a colonist "M-Hulk" exists
    And "M-Hulk" gender is male
    And Nelim's Pickle Tools: "M-Hulk" body type is Hulk
    And Nelim's Pickle Tools: "M-Hulk" stands at (202, 186) facing South
    And I draft "M-Hulk"
    And a colonist "M-Kid" exists
    And "M-Kid" is 8 years old
    And "M-Kid" gender is male
    And Nelim's Pickle Tools: "M-Kid" body type is Child
    And Nelim's Pickle Tools: "M-Kid" stands at (204, 186) facing South
    And I draft "M-Kid"
    And a colonist "F-Thin" exists
    And "F-Thin" gender is female
    And Nelim's Pickle Tools: "F-Thin" body type is Thin
    And Nelim's Pickle Tools: "F-Thin" stands at (196, 184) facing South
    And I draft "F-Thin"
    And a colonist "F-Avg" exists
    And "F-Avg" gender is female
    And Nelim's Pickle Tools: "F-Avg" body type is Female
    And Nelim's Pickle Tools: "F-Avg" stands at (198, 184) facing South
    And I draft "F-Avg"
    And a colonist "F-Fat" exists
    And "F-Fat" gender is female
    And Nelim's Pickle Tools: "F-Fat" body type is Fat
    And Nelim's Pickle Tools: "F-Fat" stands at (200, 184) facing South
    And I draft "F-Fat"
    And a colonist "F-Hulk" exists
    And "F-Hulk" gender is female
    And Nelim's Pickle Tools: "F-Hulk" body type is Hulk
    And Nelim's Pickle Tools: "F-Hulk" stands at (202, 184) facing South
    And I draft "F-Hulk"
    And a colonist "F-Kid" exists
    And "F-Kid" is 8 years old
    And "F-Kid" gender is female
    And Nelim's Pickle Tools: "F-Kid" body type is Child
    And Nelim's Pickle Tools: "F-Kid" stands at (204, 184) facing South
    And I draft "F-Kid"
    And I destroy the gear of "M-Thin"
    And I destroy the gear of "M-Avg"
    And I destroy the gear of "M-Fat"
    And I destroy the gear of "M-Hulk"
    And I destroy the gear of "M-Kid"
    And I destroy the gear of "F-Thin"
    And I destroy the gear of "F-Avg"
    And I destroy the gear of "F-Fat"
    And I destroy the gear of "F-Hulk"
    And I destroy the gear of "F-Kid"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "outline shirt, South, bare"
    And I destroy the gear of "M-Thin"
    And Nelim's Pickle Tools: "M-Thin" wears "UnderWhere_Boxers"
    And I destroy the gear of "M-Avg"
    And Nelim's Pickle Tools: "M-Avg" wears "UnderWhere_Boxers"
    And I destroy the gear of "M-Fat"
    And Nelim's Pickle Tools: "M-Fat" wears "UnderWhere_Boxers"
    And I destroy the gear of "M-Hulk"
    And Nelim's Pickle Tools: "M-Hulk" wears "UnderWhere_Boxers"
    And I destroy the gear of "M-Kid"
    And Nelim's Pickle Tools: "M-Kid" wears "UnderWhere_Loincloth"
    And I destroy the gear of "F-Thin"
    And Nelim's Pickle Tools: "F-Thin" wears "UnderWhere_Panties"
    And I destroy the gear of "F-Avg"
    And Nelim's Pickle Tools: "F-Avg" wears "UnderWhere_Panties"
    And I destroy the gear of "F-Fat"
    And Nelim's Pickle Tools: "F-Fat" wears "UnderWhere_Panties"
    And I destroy the gear of "F-Hulk"
    And Nelim's Pickle Tools: "F-Hulk" wears "UnderWhere_Panties"
    And I destroy the gear of "F-Kid"
    And Nelim's Pickle Tools: "F-Kid" wears "UnderWhere_Loincloth"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "outline shirt, South, underwear"
    And Nelim's Pickle Tools: "M-Thin" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-Fat" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-Hulk" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-Thin" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-Avg" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-Fat" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-Hulk" wears "Apparel_BasicShirt"
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_BasicShirt"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "outline shirt, South, T-shirt"
