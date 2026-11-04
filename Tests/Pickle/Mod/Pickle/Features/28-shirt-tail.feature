# The vanilla button shirt moved onto the WDI Male body (Virginie, 2026-11-05: the C' shirt tail judged good on the
# prototype boards, now the same in game). Three Male pawns, one per facing, in the frame of 26-nude-front: the shirt
# alone, then the shirt with AB's trousers. Pass: wsl-deps.shirt-tail.map, whose test-only mod supplies the textures.
@review @shirt-tail @timeout:600
Feature: the transferred button shirt on the WDI Male body, three facings

  Background:
    Given the save "Nelims-tribe" is loaded
    And game speed is paused

  @requires:wdi.realistic.bodies @requires:nelim.venustouch.waistlines.shirttailproto @requires:nelim.pickletools.textureowner @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario: the button shirt, then the shirt with trousers (South, East, North)
    Then Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Male_south" is answered by the mod "nelim.venustouch.waistlines.shirttailproto"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Male_east" is answered by the mod "nelim.venustouch.waistlines.shirttailproto"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Male_north" is answered by the mod "nelim.venustouch.waistlines.shirttailproto"
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
    And Nelim's Pickle Tools: "M-South" wears "Apparel_ShirtButton"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_ShirtButton"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_ShirtButton"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 120 ticks
    And I take a screenshot "button shirt alone"
    And Nelim's Pickle Tools: "M-South" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-East" wears "Apparel_Pants"
    And Nelim's Pickle Tools: "M-North" wears "Apparel_Pants"
    And I wait 120 ticks
    And I take a screenshot "button shirt with trousers"
