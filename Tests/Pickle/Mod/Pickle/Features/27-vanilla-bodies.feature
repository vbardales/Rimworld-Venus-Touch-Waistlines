# The vanilla body and Core shirt textures written as PNG (Virginie, 2026-11-02): to stretch the vanilla body onto the WDI body and find where a garment drawn for vanilla must be modified.
# Pass: wsl-deps.vanilla-bodies.map. The files land in the report's screenshots folder as pickletools-texture-save--<name>.png.
@vanilla-bodies @timeout:300
Feature: the vanilla body and shirt textures saved as PNG

  Background:
    Given the save "test-colony" is loaded
    And game speed is paused

  @requires:nelim.pickletools.textureowner
  Scenario: the six vanilla bodies, three facings, and the Core shirt, front
    When Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Male_south" is saved as "vanilla-male-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Male_north" is saved as "vanilla-male-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Male_east" is saved as "vanilla-male-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Female_south" is saved as "vanilla-female-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Female_north" is saved as "vanilla-female-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Female_east" is saved as "vanilla-female-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Thin_south" is saved as "vanilla-thin-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Thin_north" is saved as "vanilla-thin-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Thin_east" is saved as "vanilla-thin-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Fat_south" is saved as "vanilla-fat-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Fat_north" is saved as "vanilla-fat-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Fat_east" is saved as "vanilla-fat-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Hulk_south" is saved as "vanilla-hulk-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Hulk_north" is saved as "vanilla-hulk-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Hulk_east" is saved as "vanilla-hulk-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Child_south" is saved as "vanilla-child-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Child_north" is saved as "vanilla-child-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Bodies/Naked_Child_east" is saved as "vanilla-child-east"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Male_south" is saved as "vanilla-shirt-male-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Female_south" is saved as "vanilla-shirt-female-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Thin_south" is saved as "vanilla-shirt-thin-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Fat_south" is saved as "vanilla-shirt-fat-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Hulk_south" is saved as "vanilla-shirt-hulk-south"

  # Virginie, 2026-11-03: the child shirt too, cut on the fundoshi line. Children cannot wear ShirtBasic: their shirt is Biotech Apparel_KidShirt (wornGraphicPath KidShirt/KidShirt + _Child).
  @requires:nelim.pickletools.textureowner
  Scenario: the Biotech kid shirt, three facings
    When Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/KidShirt/KidShirt_Child_south" is saved as "vanilla-kidshirt-child-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/KidShirt/KidShirt_Child_north" is saved as "vanilla-kidshirt-child-north"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/KidShirt/KidShirt_Child_east" is saved as "vanilla-kidshirt-child-east"

  # Virginie, 2026-11-03: vanilla to WDI, navel and chest: garments with a shape, to see how WDI stretches them (WDI ships both for Thin/Fat/Hulk_Female).
  @requires:nelim.pickletools.textureowner
  Scenario: the button shirt and the royal corset, front
    When Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Male_south" is saved as "vanilla-shirtbutton-male-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Female_south" is saved as "vanilla-shirtbutton-female-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Thin_south" is saved as "vanilla-shirtbutton-thin-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Fat_south" is saved as "vanilla-shirtbutton-fat-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/ShirtButton/ShirtButton_Hulk_south" is saved as "vanilla-shirtbutton-hulk-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/CorsetRoyal/CorsetRoyal_Male_south" is saved as "vanilla-corsetroyal-male-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/CorsetRoyal/CorsetRoyal_Female_south" is saved as "vanilla-corsetroyal-female-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/CorsetRoyal/CorsetRoyal_Thin_south" is saved as "vanilla-corsetroyal-thin-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/CorsetRoyal/CorsetRoyal_Fat_south" is saved as "vanilla-corsetroyal-fat-south"
    And Nelim's Pickle Tools: the texture "Things/Pawn/Humanlike/Apparel/CorsetRoyal/CorsetRoyal_Hulk_south" is saved as "vanilla-corsetroyal-hulk-south"
