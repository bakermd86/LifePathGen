from enum import Enum


class Skills(Enum):
    acrobatics = 'Acrobatics'
    melee = 'Melee'
    stealth = 'Stealth'
    parry = 'Parry'
    ranged_weapons = 'Ranged Weapons'
    sailing = 'Sailing'
    insight = 'Insight'
    observation = 'Observation'
    survival = 'Survival'
    thievery = 'Thievery'
    alchemy = 'Alchemy'
    craft = 'Craft'
    healing = 'Healing'
    linguistics = 'Linguistics'
    warfare = 'Warfare'
    lore = 'Lore'
    athletics = 'Athletics'
    resistance = 'Resistance'
    discipline = 'Discipline'
    sorcery = 'Sorcery'
    animal_handling = 'Animal Handling'
    command = 'Command'
    counsel = 'Counsel'
    persuade = 'Persuade'
    society = 'Society'


class Attributes(Enum):
    agility = 'Agility'
    coordination = 'Coordination'
    awareness = 'Awareness'
    intelligence = 'Intelligence'
    brawn = 'Brawn'
    willpower = 'Willpower'
    personality = 'Personality'


att_map = {Attributes.agility: (Skills.acrobatics, Skills.melee, Skills.stealth),
           Attributes.coordination: (Skills.parry, Skills.ranged_weapons, Skills.sailing),
           Attributes.awareness: (Skills.insight, Skills.observation, Skills.survival, Skills.thievery),
           Attributes.intelligence: (Skills.alchemy, Skills.craft, Skills.healing, Skills.linguistics, Skills.warfare, Skills.lore),
           Attributes.brawn: (Skills.athletics, Skills.resistance),
           Attributes.willpower: (Skills.discipline, Skills.sorcery),
           Attributes.personality: (Skills.animal_handling, Skills.command, Skills.counsel, Skills.persuade, Skills.society),
           }

skill_map = {Skills.acrobatics: Attributes.agility,
             Skills.melee: Attributes.agility,
             Skills.stealth: Attributes.agility,
             Skills.parry: Attributes.coordination,
             Skills.ranged_weapons: Attributes.coordination,
             Skills.sailing: Attributes.coordination,
             Skills.insight: Attributes.awareness,
             Skills.observation: Attributes.awareness,
             Skills.survival: Attributes.awareness,
             Skills.thievery: Attributes.awareness,
             Skills.alchemy: Attributes.intelligence,
             Skills.craft: Attributes.intelligence,
             Skills.healing: Attributes.intelligence,
             Skills.linguistics: Attributes.intelligence,
             Skills.warfare: Attributes.intelligence,
             Skills.lore: Attributes.intelligence,
             Skills.athletics: Attributes.brawn,
             Skills.resistance: Attributes.brawn,
             Skills.discipline: Attributes.willpower,
             Skills.sorcery: Attributes.willpower,
             Skills.animal_handling: Attributes.personality,
             Skills.command: Attributes.personality,
             Skills.counsel: Attributes.personality,
             Skills.persuade: Attributes.personality,
             Skills.society: Attributes.personality,
             }
