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
        "name": "Vaelith Shadowweaver",
        "race": "Dark Elf",
        "class": "Sorcerer",
        "max_hp": 28,
        "gold": 150,
        "xp": 0,
        "level": 1,
        "mana": 15,
        "inventory": [
            "Spellbook",
            "Dagger",
            "Potion of Healing",
            "Dark Cloak"
        ],
        "equipped_weapon": "Dagger",
        "alignment_righteousness": "Neutral",
        "alignment_morality": "Evil",
        "birthplace": "Underdark",
        "skills": [],
        "description": "A cunning and mysterious dark elf sorcerer, adept in the arcane arts and skilled in the shadows.",
        "stats": {
            "STR": 8,
            "CON": 10,
            "DEX": 14,
            "INT": 16,
            "WIS": 12,
            "CHA": 10
        }
    }