from enum import Enum
import json

class Character:

    def __init__(self, json):
        """
        Character constructor.
        
        Args:
            json: takes the json string generated from AI (or maybe from input in the future)
        """
        self.json = json
    
    def __getitem__(self, key):
        return self.json[key]

test_character_json = {
  "name": "Vaelith Shadowbane",
  "race": "Dark Elf",
  "class": "Warrior",
  "max_hp": 85,
  "gold": 150,
  "xp": 1200,
  "level": 5,
  "mana": 120,
  "inventory": [
    "Spellbook of Shadows",
    "Potion of Dark Vision",
    "Obsidian Dagger",
    "Cloak of Shadows",
    "Longbow"
  ],
  "equipped_weapon": "Longbow",
  "alignment_righteousness": "Evil",
  "alignment_morality": "Chaotic",
  "birthplace": "The Underdark",
  "skills": [
    "Fireball",
    "Crippling Curse",
    "Frost Bite"
  ],
  "description": "A mysterious and cunning dark elf who wields forbidden magic, Vaelith Shadowbane is feared for his mastery over dark spells and his ruthless tactics in battle.",
  "stats": {
    "STR": 8,
    "CON": 10,
    "DEX": 12,
    "INT": 14,
    "WIS": 9,
    "CHA": 12
  }
}