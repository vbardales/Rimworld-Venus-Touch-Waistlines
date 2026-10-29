# Does Children Wear Anything rescale the outline on a child? (Virginie, 2026-10-29: "ca fait du retaillage pour enfants")
# One adult for reference, two children, shirt + trousers + the red outline top, from the front and the side.
# Played twice with the same filter: pass wsl-deps.wdi-outline.map (CWA at its defaults: rotation, scaling, body and tattoo scaling on)
# and pass wsl-deps.wdi-outline-cwaoff.map (same mods, config/wdi-outline-cwaoff turns the four CWA effects off). Compare the kids.
@review @cwa-kids @timeout:600
Feature: the outline on a child with and without the Children Wear Anything rescaling

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:wdi.realistic.bodies @requires:LoneKin.ChildrenWearAnything @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: an adult and two children, shirt, trousers and outline top, front (South)
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-Avg" exists
    And "M-Avg" gender is male
    And Nelim's Pickle Tools: "M-Avg" body type is Male
    And Nelim's Pickle Tools: "M-Avg" stands at (198, 186) facing South
    And I draft "M-Avg"
    And a colonist "M-Kid" exists
    And "M-Kid" is 8 years old
    And "M-Kid" gender is male
    And Nelim's Pickle Tools: "M-Kid" body type is Child
    And Nelim's Pickle Tools: "M-Kid" stands at (204, 186) facing South
    And I draft "M-Kid"
    And a colonist "F-Kid" exists
    And "F-Kid" is 8 years old
    And "F-Kid" gender is female
    And Nelim's Pickle Tools: "F-Kid" body type is Child
    And Nelim's Pickle Tools: "F-Kid" stands at (204, 184) facing South
    And I draft "F-Kid"
    And I destroy the gear of "M-Avg"
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "M-Avg" wears "Venus_TestOutlineTop"
    And I destroy the gear of "M-Kid"
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "M-Kid" wears "Venus_TestOutlineTop"
    And I destroy the gear of "F-Kid"
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "F-Kid" wears "Venus_TestOutlineTop"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "cwa kids, front, shirt and trousers and outline top"

  @requires:wdi.realistic.bodies @requires:LoneKin.ChildrenWearAnything @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: an adult and two children, shirt, trousers and outline top, side (East)
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-Avg" exists
    And "M-Avg" gender is male
    And Nelim's Pickle Tools: "M-Avg" body type is Male
    And Nelim's Pickle Tools: "M-Avg" stands at (198, 186) facing East
    And I draft "M-Avg"
    And a colonist "M-Kid" exists
    And "M-Kid" is 8 years old
    And "M-Kid" gender is male
    And Nelim's Pickle Tools: "M-Kid" body type is Child
    And Nelim's Pickle Tools: "M-Kid" stands at (204, 186) facing East
    And I draft "M-Kid"
    And a colonist "F-Kid" exists
    And "F-Kid" is 8 years old
    And "F-Kid" gender is female
    And Nelim's Pickle Tools: "F-Kid" body type is Child
    And Nelim's Pickle Tools: "F-Kid" stands at (204, 184) facing East
    And I draft "F-Kid"
    And I destroy the gear of "M-Avg"
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "M-Avg" wears "Venus_TestOutlineTop"
    And I destroy the gear of "M-Kid"
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "M-Kid" wears "Venus_TestOutlineTop"
    And I destroy the gear of "F-Kid"
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Pickle Tools: "F-Kid" wears "Venus_TestOutlineTop"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "cwa kids, side, shirt and trousers and outline top"
