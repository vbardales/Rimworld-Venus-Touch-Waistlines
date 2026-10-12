@review @underwear-comparison @timeout:300
Feature: WDI underwear under a t-shirt and trousers, from every facing

  Background:
    Given the save "Nelims-tribe" is loaded

  @requires:wdi.realistic.bodies @requires:Malistaticy.UnderWhere @requires:ab.vplrf @requires:nelim.pickletools.screenshotstudio @requires:nelim.pickletools.colonistrace
  Scenario Outline: ten silhouettes wear their WDI underwear under trousers, facing <facing>
    Given Nelim's Sanctuary: the animals are removed from the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: the other colonists are out of frame
    And a colonist "M-Thin" exists
    And "M-Thin" gender is male
    And Nelim's Pickle Tools: "M-Thin" body type is Thin
    And a colonist "M-Avg" exists
    And "M-Avg" gender is male
    And Nelim's Pickle Tools: "M-Avg" body type is Male
    And a colonist "M-Fat" exists
    And "M-Fat" gender is male
    And Nelim's Pickle Tools: "M-Fat" body type is Fat
    And a colonist "M-Hulk" exists
    And "M-Hulk" gender is male
    And Nelim's Pickle Tools: "M-Hulk" body type is Hulk
    And a colonist "M-Kid" exists
    And "M-Kid" is 8 years old
    And "M-Kid" gender is male
    And Nelim's Pickle Tools: "M-Kid" body type is Child
    And a colonist "F-Thin" exists
    And "F-Thin" gender is female
    And Nelim's Pickle Tools: "F-Thin" body type is Thin
    And a colonist "F-Avg" exists
    And "F-Avg" gender is female
    And Nelim's Pickle Tools: "F-Avg" body type is Female
    And a colonist "F-Fat" exists
    And "F-Fat" gender is female
    And Nelim's Pickle Tools: "F-Fat" body type is Fat
    And a colonist "F-Hulk" exists
    And "F-Hulk" gender is female
    And Nelim's Pickle Tools: "F-Hulk" body type is Hulk
    And a colonist "F-Kid" exists
    And "F-Kid" is 8 years old
    And "F-Kid" gender is female
    And Nelim's Pickle Tools: "F-Kid" body type is Child
    And Nelim's Pickle Tools: "M-Thin" stands at (196, 186) facing <facing>
    And I draft "M-Thin"
    And Nelim's Pickle Tools: "M-Avg" stands at (198, 186) facing <facing>
    And I draft "M-Avg"
    And Nelim's Pickle Tools: "M-Fat" stands at (200, 186) facing <facing>
    And I draft "M-Fat"
    And Nelim's Pickle Tools: "M-Hulk" stands at (202, 186) facing <facing>
    And I draft "M-Hulk"
    And Nelim's Pickle Tools: "M-Kid" stands at (204, 186) facing <facing>
    And I draft "M-Kid"
    And Nelim's Pickle Tools: "F-Thin" stands at (196, 184) facing <facing>
    And I draft "F-Thin"
    And Nelim's Pickle Tools: "F-Avg" stands at (198, 184) facing <facing>
    And I draft "F-Avg"
    And Nelim's Pickle Tools: "F-Fat" stands at (200, 184) facing <facing>
    And I draft "F-Fat"
    And Nelim's Pickle Tools: "F-Hulk" stands at (202, 184) facing <facing>
    And I draft "F-Hulk"
    And Nelim's Pickle Tools: "F-Kid" stands at (204, 184) facing <facing>
    And I draft "F-Kid"
    And I destroy the gear of "M-Thin"
    And Nelim's Pickle Tools: "M-Thin" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Thin" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Thin" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Avg"
    And Nelim's Pickle Tools: "M-Avg" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Fat"
    And Nelim's Pickle Tools: "M-Fat" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Fat" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Fat" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Hulk"
    And Nelim's Pickle Tools: "M-Hulk" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Hulk" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Hulk" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Kid"
    And Nelim's Pickle Tools: "M-Kid" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Thin"
    And Nelim's Pickle Tools: "F-Thin" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Thin" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Thin" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Avg"
    And Nelim's Pickle Tools: "F-Avg" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Fat"
    And Nelim's Pickle Tools: "F-Fat" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Fat" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Fat" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Hulk"
    And Nelim's Pickle Tools: "F-Hulk" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Hulk" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Hulk" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Kid"
    And Nelim's Pickle Tools: "F-Kid" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Thin"
    And Nelim's Pickle Tools: "M-Thin" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Thin" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Avg"
    And Nelim's Pickle Tools: "M-Avg" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Fat"
    And Nelim's Pickle Tools: "M-Fat" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Fat" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Hulk"
    And Nelim's Pickle Tools: "M-Hulk" wears "UnderWhere_Boxers" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Hulk" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "M-Kid"
    And Nelim's Pickle Tools: "M-Kid" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Thin"
    And Nelim's Pickle Tools: "F-Thin" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Thin" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Avg"
    And Nelim's Pickle Tools: "F-Avg" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Avg" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Fat"
    And Nelim's Pickle Tools: "F-Fat" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Fat" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Hulk"
    And Nelim's Pickle Tools: "F-Hulk" wears "UnderWhere_Panties" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Hulk" wears "Apparel_Pants" dyed rgb (46, 74, 120)
    And I destroy the gear of "F-Kid"
    And Nelim's Pickle Tools: "F-Kid" wears "UnderWhere_Loincloth" dyed rgb (214, 160, 82)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidPants" dyed rgb (46, 74, 120)
    And Nelim's Sanctuary: I am at the sanctuary "calm-zone-close"
    And Nelim's Pickle Tools: studio presentation mode is enabled
    And I wait 90 ticks
    And Nelim's Pickle Tools: "M-Thin" faces <facing>
    And Nelim's Pickle Tools: "M-Avg" faces <facing>
    And Nelim's Pickle Tools: "M-Fat" faces <facing>
    And Nelim's Pickle Tools: "M-Hulk" faces <facing>
    And Nelim's Pickle Tools: "M-Kid" faces <facing>
    And Nelim's Pickle Tools: "F-Thin" faces <facing>
    And Nelim's Pickle Tools: "F-Avg" faces <facing>
    And Nelim's Pickle Tools: "F-Fat" faces <facing>
    And Nelim's Pickle Tools: "F-Hulk" faces <facing>
    And Nelim's Pickle Tools: "F-Kid" faces <facing>
    And I wait 2 ticks
    And I take a screenshot "underwear comparison, <facing>, bare torso and trousers"
    And Nelim's Pickle Tools: "M-Thin" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Fat" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Hulk" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "M-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Thin" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Avg" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Fat" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Hulk" wears "Apparel_BasicShirt" dyed rgb (230, 224, 206)
    And Nelim's Pickle Tools: "F-Kid" wears "Apparel_KidShirt" dyed rgb (230, 224, 206)
    And I wait 90 ticks
    And I take a screenshot "underwear comparison, <facing>, t-shirt and trousers"
    Then no warning matching "Could not load UnityEngine.Texture2D" was logged
    And no warning matching "Failed to find any textures" was logged

    Examples:
      | facing |
      | South  |
      | East   |
      | North  |
