@review @private-lewd-wdi @timeout:420
Feature: private LEWD-derived textures on all WDI profiles without Hooman Cute

  Background:
    Given the save "Nelims-tribe" is loaded

  @requires:wdi.realistic.bodies @requires:nelim.private.lewd-wdi-textures @requires:LoneKin.ChildrenWearAnything @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace @requires:nelim.pickletools.camerazoom @requires:nelim.pickletools.clickdiagnostics
  Scenario: LEWD texture-only WDI pack resolves every human silhouette
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-Thin" exists
    And "M-Thin" gender is male
    And Nelim's Pickle Tools: "M-Thin" body type is Thin
    And Nelim's Pickle Tools: "M-Thin" stands at (196, 186) facing South
    And a colonist "M-Avg" exists
    And "M-Avg" gender is male
    And Nelim's Pickle Tools: "M-Avg" body type is Male
    And Nelim's Pickle Tools: "M-Avg" stands at (198, 186) facing South
    And a colonist "M-Fat" exists
    And "M-Fat" gender is male
    And Nelim's Pickle Tools: "M-Fat" body type is Fat
    And Nelim's Pickle Tools: "M-Fat" stands at (200, 186) facing South
    And a colonist "M-Hulk" exists
    And "M-Hulk" gender is male
    And Nelim's Pickle Tools: "M-Hulk" body type is Hulk
    And Nelim's Pickle Tools: "M-Hulk" stands at (202, 186) facing South
    And a colonist "M-Kid" exists
    And "M-Kid" is 8 years old
    And "M-Kid" gender is male
    And Nelim's Pickle Tools: "M-Kid" body type is Child
    And Nelim's Pickle Tools: "M-Kid" stands at (204, 186) facing South
    And a colonist "F-Thin" exists
    And "F-Thin" gender is female
    And Nelim's Pickle Tools: "F-Thin" body type is Thin
    And Nelim's Pickle Tools: "F-Thin" stands at (196, 184) facing South
    And a colonist "F-Avg" exists
    And "F-Avg" gender is female
    And Nelim's Pickle Tools: "F-Avg" body type is Female
    And Nelim's Pickle Tools: "F-Avg" stands at (198, 184) facing South
    And a colonist "F-Fat" exists
    And "F-Fat" gender is female
    And Nelim's Pickle Tools: "F-Fat" body type is Fat
    And Nelim's Pickle Tools: "F-Fat" stands at (200, 184) facing South
    And a colonist "F-Hulk" exists
    And "F-Hulk" gender is female
    And Nelim's Pickle Tools: "F-Hulk" body type is Hulk
    And Nelim's Pickle Tools: "F-Hulk" stands at (202, 184) facing South
    And a colonist "F-Kid" exists
    And "F-Kid" is 8 years old
    And "F-Kid" gender is female
    And Nelim's Pickle Tools: "F-Kid" body type is Child
    And Nelim's Pickle Tools: "F-Kid" stands at (204, 184) facing South
    And I draft "M-Thin"
    And I draft "M-Avg"
    And I draft "M-Fat"
    And I draft "M-Hulk"
    And I draft "M-Kid"
    And I draft "F-Thin"
    And I draft "F-Avg"
    And I draft "F-Fat"
    And I draft "F-Hulk"
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
    And Nelim's Pickle Tools: "M-Thin" wears "LEWDWDI_Apparel_TubeTop"
    And Nelim's Pickle Tools: "M-Avg" wears "LEWDWDI_Apparel_TubeTop"
    And Nelim's Pickle Tools: "M-Fat" wears "LEWDWDI_Apparel_TubeTop"
    And Nelim's Pickle Tools: "M-Hulk" wears "LEWDWDI_Apparel_TubeTop"
    And Nelim's Pickle Tools: "M-Kid" wears "LEWDWDI_Apparel_TubeTop"
    And Nelim's Pickle Tools: "F-Thin" wears "LEWDWDI_Apparel_FlakiniVest"
    And Nelim's Pickle Tools: "F-Avg" wears "LEWDWDI_Apparel_FlakiniVest"
    And Nelim's Pickle Tools: "F-Fat" wears "LEWDWDI_Apparel_FlakiniVest"
    And Nelim's Pickle Tools: "F-Hulk" wears "LEWDWDI_Apparel_FlakiniVest"
    And Nelim's Pickle Tools: "F-Kid" wears "LEWDWDI_Apparel_FlakiniVest"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And Nelim's Pickle Tools: the camera is centered on "M-Fat" at root size 11
    And I take a screenshot "private LEWD WDI, south"
    And Nelim's Pickle Tools: "M-Thin" faces East
    And Nelim's Pickle Tools: "M-Avg" faces East
    And Nelim's Pickle Tools: "M-Fat" faces East
    And Nelim's Pickle Tools: "M-Hulk" faces East
    And Nelim's Pickle Tools: "M-Kid" faces East
    And Nelim's Pickle Tools: "F-Thin" faces East
    And Nelim's Pickle Tools: "F-Avg" faces East
    And Nelim's Pickle Tools: "F-Fat" faces East
    And Nelim's Pickle Tools: "F-Hulk" faces East
    And Nelim's Pickle Tools: "F-Kid" faces East
    And I wait 120 ticks
    And Nelim's Pickle Tools: the camera is centered on "M-Fat" at root size 11
    And I take a screenshot "private LEWD WDI, east"
    And Nelim's Pickle Tools: "M-Thin" faces North
    And Nelim's Pickle Tools: "M-Avg" faces North
    And Nelim's Pickle Tools: "M-Fat" faces North
    And Nelim's Pickle Tools: "M-Hulk" faces North
    And Nelim's Pickle Tools: "M-Kid" faces North
    And Nelim's Pickle Tools: "F-Thin" faces North
    And Nelim's Pickle Tools: "F-Avg" faces North
    And Nelim's Pickle Tools: "F-Fat" faces North
    And Nelim's Pickle Tools: "F-Hulk" faces North
    And Nelim's Pickle Tools: "F-Kid" faces North
    And I wait 120 ticks
    And Nelim's Pickle Tools: the camera is centered on "M-Fat" at root size 11
    And I take a screenshot "private LEWD WDI, north"
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
    And Nelim's Pickle Tools: "M-Thin" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "M-Avg" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "M-Fat" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "M-Hulk" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "M-Kid" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "F-Thin" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "F-Avg" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "F-Fat" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "F-Hulk" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: "F-Kid" wears "LEWDWDI_Apparel_MicroSkirt"
    And I wait 120 ticks
    And Nelim's Pickle Tools: the camera is centered on "M-Fat" at root size 11
    And I take a screenshot "private LEWD WDI mini-skirt, north"
    Then no warning matching "Failed to find any textures" was logged
    And no warning matching "Could not load UnityEngine.Texture2D" was logged
