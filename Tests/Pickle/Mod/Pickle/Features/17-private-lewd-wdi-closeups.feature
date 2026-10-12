@review @private-lewd-wdi @timeout:420
Feature: private LEWD-derived textures in close-up on every adult WDI silhouette

  Background:
    Given the save "Nelims-tribe" is loaded

  @requires:wdi.realistic.bodies @requires:nelim.private.lewd-wdi-textures @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace @requires:nelim.pickletools.camerazoom
  Scenario Outline: an adult WDI silhouette wears its private LEWD-derived garment in three orientations
    Given Nelim's Sanctuary: the animals are kept out of the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "<pawn>" exists
    And "<pawn>" gender is <gender>
    And Nelim's Pickle Tools: "<pawn>" body type is <body>
    And Nelim's Pickle Tools: "<pawn>" stands at (200, 185) facing South
    And I destroy the gear of "<pawn>"
    And Nelim's Pickle Tools: "<pawn>" wears "<top>"
    And I draft "<pawn>"
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And Nelim's Pickle Tools: the camera is centered on "<pawn>" at root size 11
    And I take a screenshot "private LEWD WDI close <profile>, south"
    And Nelim's Pickle Tools: "<pawn>" faces East
    And Nelim's Pickle Tools: the camera is centered on "<pawn>" at root size 11
    And I take a screenshot "private LEWD WDI close <profile>, east"
    And Nelim's Pickle Tools: "<pawn>" faces North
    And Nelim's Pickle Tools: the camera is centered on "<pawn>" at root size 11
    And I take a screenshot "private LEWD WDI close <profile>, north"
    And I destroy the gear of "<pawn>"
    And Nelim's Pickle Tools: "<pawn>" wears "LEWDWDI_Apparel_MicroSkirt"
    And Nelim's Pickle Tools: the camera is centered on "<pawn>" at root size 11
    And I take a screenshot "private LEWD WDI close <profile>, mini-skirt north"
    Then no warning matching "Failed to find any textures" was logged

    Examples:
      | profile      | pawn      | gender | body   | top                          |
      | Male         | Close-M   | male   | Male   | LEWDWDI_Apparel_TubeTop      |
      | Male_Thin    | Close-MT  | male   | Thin   | LEWDWDI_Apparel_TubeTop      |
      | Male_Hulk    | Close-MH  | male   | Hulk   | LEWDWDI_Apparel_TubeTop      |
      | Male_Fat     | Close-MF  | male   | Fat    | LEWDWDI_Apparel_TubeTop      |
      | Female       | Close-F   | female | Female | LEWDWDI_Apparel_FlakiniVest  |
      | Female_Thin  | Close-FT  | female | Thin   | LEWDWDI_Apparel_FlakiniVest  |
      | Female_Hulk  | Close-FH  | female | Hulk   | LEWDWDI_Apparel_FlakiniVest  |
      | Female_Fat   | Close-FF  | female | Fat    | LEWDWDI_Apparel_FlakiniVest  |

