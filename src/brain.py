from openai import OpenAI
from dotenv import load_dotenv
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import time
import re
import json
import random

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
json_path = BASE_DIR / "json_exp"
skill_path = json_path / "skill.json"
item_path = json_path / "item.json"
enemy_path = json_path / "enemies.json"




# Load the .env file -> so it takes the api key (remember to create it)
load_dotenv()

# Client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Fall back to call if another free model is not available
FREE_MODELS = [
    "mistralai/devstral-2512:free", # Damn Frog Eater from the other side of the Apls
    "nex-agi/deepseek-v3.1-nex-n1:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3n-e2b-it:free",
    "meta-llama/llama-guard-4-12b:free",
    "openrouter/auto"
]

# Global variables for long-term memory management 
system_rules =  {
            "role": "system",
            "content": """You are the master of a D&D-style fantasy text adventure.
                            You must ALWAYS respond in valid JSON, with this structure:

        {
        "narration": "describe the scene immersively",
        "found_items": [],
        "lost_items": [],
        "location": "current location of the player",
        "quest": "current quest of the player",
        "max_hp_change": 0,
        "xp_gained": 0,
        "gold_change": 0,
        "encounter": false
        }

        Rules:
        - ALWAYS respond in English!
        - narration: narrative text only
        - If the player talks to an NPC, include the dialogue in narration.
        - found_items: items found by the player (add to inventory)
        - lost_items: lost items (remove from inventory)
        - location/quest: update state if changed
        - encounter: true if a combat encounter starts
        - use negative numbers for losses, positive for gains
        - xp could be gainend only after combat
        - Never decide for the player
        - Output ONLY raw JSON
        - Do NOT use markdown
        - Do NOT add explanations
        - Do NOT wrap the JSON in ``` fences
        - Output must start with { and end with }
        """
}

alignment_prompt = {
    "role": "system",
    "content": """
The player character has a moral alignment and a righteousness alignment.

alignment_morality:
- good: compassionate, altruistic, avoids cruelty
- neutral: pragmatic, self-interested but not malicious
- evil: cruel, selfish, enjoys or accepts suffering

alignment_righteousness:
- lawful: respects rules, traditions, authority
- neutral: flexible, situational ethics
- chaotic: distrusts authority, values freedom over order

INSTRUCTIONS:
- USE ONLY the ALIGNMENT described here, do NOT invent new alignments.
- Always narrate the world, NPC reactions, and consequences in a way consistent with the character's alignments.
- Do NOT change the character's alignment unless explicitly instructed by the system.
- Do NOT force actions; only influence tone, outcomes, and reactions.
- If the player acts strongly against alignment, show narrative tension or consequences.
- If the player acts passively against alignment, show internal conflict or doubt.
- If the player acts in a way that is extremely against their alignment, the action cannot be performed outright unless there are extreme circumstances.
"""
}




turn_count = 0
recent_history = []
#! Make sure to change the start point, so you can get the places from the approved database
long_term_memory = "The character is located in the Initial Tavern. No relevant events so far."
mana_regen_per_turn = 5  # Adjust regeneration rate if desired


# 3 tries for models distanced by a 2 second delay each one then fallback to the next one
def narrate(history, retries=3, delay=2):
    for model in FREE_MODELS:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=history,
                    max_tokens=400,
                    # temperature=0.7   # Tested but not used for now (https://openrouter.ai/docs/api/reference/parameters)
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[WARN] Model {model} failed attempt {attempt+1}: {e}")
                time.sleep(delay)
        print(f"[INFO] Passing to next model...")

    return "The narrator is temporarily out of voice. Please try again shortly."


# We cannot trust the model to always return valid JSON, so we need to extract it from the text
def extract_json(text):
    # I stole this, don't judge me. Regrex are black magic to me! :-(
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("No found JASON object in the text")
    return json.loads(match.group())




# Inspiration: Claude playing Pokémon (too complicated to implement here)
# from point to maxthokens (point2) -> summary1 
# from point2 to maxthokens (point3) -> summary2
# Context saved: summary1 + summary2 + recent messages (?)

# Summarises the long-term memory by extracting the most important events from recent history
# Updates the memory so the AI can maintain context without exceeding token limits
# Returns a concise summary of the adventure to be used in future turns
def summarise_memory(long_memory, recent_history):
    messages = [
            {"role": "system", "content": "You are a reporter. Summarise the most important facts of the adventure."},
            {"role": "user", "content": f"Current memory: {long_memory}\n Recent events: {recent_history}\n Update memory with new facts."}
        ]

    # Call the model to get the summary
    summary = narrate(messages)

    try:
        data = extract_json(summary)
        return data.get("narration", summary)
    except:
        return summary


# Utility function to update stats with bounds
def update_stat(current, change, min_val=0, max_val=9999):
    return max(min_val, min(max_val, current + change))

# Use the AI to generate a full character sheet JSON based on a free-text description.
def create_character_from_description(description: str) -> dict:
    # Load the approved skills from skill.json
    with open(skill_path, "r", encoding="utf-8") as f:
        skills_db = json.load(f)
    with open(item_path, "r", encoding="utf-8") as f:
        items_db = json.load(f)
    
    skill_options = [f"- {s['name']} (Type: {s['type']}, Min Level: {s['min_lv']}): {s['description']}" for s in skills_db]
    available_skills_text = "\n".join(skill_options)
    

    prompt = [
            {"role": "system", "content": "You are a character creation AI. Generate a complete D&D-style character sheet in JSON format."},
            {"role": "user", "content": f"""
        Create a character sheet based on this description:
        {description}

        **AVAILABLE SKILLS (CHOOSE ONE FROM THESE ONLY):**
        {available_skills_text}

        Include the following fields:
        - name
        - race
        - class
        - max_hp = 50
        - gold
        - xp
        - level
        - mana
        - inventory (initially empty)
        - equipped_weapon
        - alignment_righteousness
        - alignment_morality
        - birthplace
        - skills (is a list that has to have at least one skill related to the class chosen)
        - description
        - stats (STR, CON, DEX, INT, WIS, CHA)

        **IMPORTANT RULES FOR SKILLS:**
        - You MUST use the exact names from the VALID SKILLS list above.
        - If the user asks for a 'buff', look for skills with type: buff.
        - If the user asks for a 'debuff', look for skills with type: defuff.
        - If the user asks for 'magic', look for skills with type: magic.
        - Do NOT repeat skills.

        Constraints for stats:
        - Each individual stat must be at least 5.
        - The sum of all stats must **not exceed 45**.
        - Distribute stats logically based on the character description.
        - Keep stats as integers.

        Return **only valid JSON**, without explanations or markdown. Ensure the JSON is complete and all fields are present.
        """}
        ] 

    
    try:
        output = narrate(prompt)
        character = extract_json(output)

    except Exception as e:
        print(f"[ERROR] Failed to generate character: {e}")
        print("Using placeholder character instead.")
        # Fallback placeholder
        return {
            "name": "Unknown Hero",
            "race": "Human",
            "class": "Warrior",
            "max_hp": 100,
            "gold": 50,
            "xp": 0,
            "level": 1,
            "mana": 50,
            "inventory": ["Short Sword"],
            "equipped_weapon": "Short Sword",
            "alignment_righteousness": "neutral",
            "alignment_morality": "neutral",
            "birthplace": "",
            "description": description,
            "skills": [],
            "stats": {
                "STR": 10,
                "CON": 10,
                "DEX": 10,
                "INT": 5,
                "WIS": 5,
                "CHA": 5
            }
        }
    
    # --- Assign skills from DB based on AI suggestions ---
    #? No find_most_similar_item used, because the ai already has the skills in the prompt when generated, we only need to validate
    selected_skills = []
    for skill_name in character.get("skills", []):
        # Find the skill in the skills database (case-insensitive match)
        skill = None
        for s in skills_db:
            if s["name"].lower() == skill_name.lower():
                skill = s
                break

        # Add it if it's valid and not already in the selected list
        if skill and skill["name"] not in selected_skills:
            selected_skills.append(skill["name"])

    # Fallback: if no valid skills found, pick one first matching skill
    if not selected_skills:
        for s in skills_db:
            if s["type"] in ("attack", "magic", "buff", "debuff"):
                selected_skills.append(s["name"])
                break  # pick only the first matching skill

    # Update character skills
    character["skills"] = selected_skills

    # --- Assign inventory (weapon/item) based on similarity ---
    #? We dont ask the ai to suggest anything, we use the characher description to find the closest item that fit it
    usable_items = []
    for i in items_db:
        if i["itemType"] in ("weapon", "magical", "consumable"):
            usable_items.append(i)
    
    # Find the most similar item to the character description
    best_item, similarity = find_most_similar_item(character["description"], usable_items)
    # Similarity score (not used here, but could be logged) 
    # #! TBH: we have to decide if we use it or not (could be used to invent the weapon if the similarity is too low)

    # Start inventory with the most similar item
    inventory = [best_item["name"]]

    # Scan description for extra items (max 3 non-weapons)
    extra_items_added = 0
    MAX_EXTRA_ITEMS = 3

    # Separate usable items into weapons and non-weapons
    all_non_weapon_items = []
    for item in usable_items:
        if item["itemType"] == "weapon":
            continue  # skip weapons
        if item["name"] == best_item["name"]:
            continue  # skip the already selected best item
        all_non_weapon_items.append(item)

    non_weapon_items = all_non_weapon_items

    while extra_items_added < MAX_EXTRA_ITEMS and non_weapon_items:
        # Find the most similar consumable to the character description
        next_item, sim = find_most_similar_item(character["description"], non_weapon_items)
        inventory.append(next_item["name"])
        extra_items_added += 1
        # Remove it from the pool to avoid duplicates
        non_weapon_items.remove(next_item)

    character["inventory"] = inventory

    if best_item["itemType"] in ("weapon", "magical"):
        character["equipped_weapon"] = best_item["name"]
    else:
        # Try to equip the first weapon in inventory
        for item_name in inventory:
            item = None  # default if not found
            for i in items_db:
                if i["name"] == item_name:
                    item = i
                    break  # stop at the first match

            if item and item["itemType"] == "weapon":
                character["equipped_weapon"] = item_name
                break
        else: 
            print(f"[ERROR] Failed to select a matching weapon to the description")
            character["inventory"] = "Short Sword"
            character["equipped_weapon"] = "Short Sword"

    # ----------------------------------------------------------

    # TODO: when we add the classes database, do as above
    # If equipped_weapon is not present in the weapon list, find the most similar one.
    #                                       V <- this is the name of a element of the list: used in the loop to create a list of weapon names
    if character["class"] not in [c["name"] for c in classes]:
        result = find_most_similar_item(character["class"], classes)
        most_similar = result[0]  # <-- Dictionary of the most similar weapon
        similarity = result[1]    # <-- Similarity score (not used here, but could be logged) #! TBH: we have to decide if we use it or not (could be used to invent the weapon if the similarity is too low)
        character["class"] = most_similar["name"]
    
    # Current HP for combat tracking
    character["current_hp"] = character["max_hp"]

    return character




# Finds the most similar item based on description using TF-IDF and cosine similarity
# Tutorial used: (https://www.newscatcherapi.com/blog-posts/ultimate-guide-to-text-similarity-with-python)
#! Remember to do: uv add scikit-learn
def find_most_similar_item(description, items):
    # Builds the corpus: first the character description, then all the item descriptions
    corpus = [description] + [item['description'] for item in items]
    
    # TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Calculate cosine similarity between the character description vector and vector of all items
    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Take the item with the highest similarity score
    max_index = similarity_scores.argmax()
    return items[max_index], similarity_scores[max_index]



# Example of approved classes (obviously this should be taken from the database)
#? OR we shoud just create a local classes file
classes = [
    {"name": "Warrior", "description": "Strong melee fighter, excels in physical combat."},
    {"name": "Mage", "description": "Master of magical arts, uses spells to attack and defend."},
    {"name": "Rogue", "description": "Stealthy and agile, skilled in ranged attacks and evasion."},
    {"name": "ranger", "description": "Expert in ranged combat and survival skills."}
]


# TODO: Skills that do danamge add this damange to the overlall damage of the weapon equipped (if any)
# if a skill do damage (min-max damange -> dice: of the skill do a max damange of 6 we use a d6, if 12 it does a d12), if it doesnt it has NULL as 0 damage
# if there a buff or debuff: we lunch a dice (i dont )
# force and intelligence could affect the damage of physical and magical weapons/skills
# DEX is used to eccet chance to hit or not be hit and the one that starts first the turn in combat
# if we want to add more complexity to attack we can add radius (so it can hit multiple enemies)

def roll_d6():
    return random.randint(1, 6)

def roll_d8():
    return random.randint(1, 8)

def roll_d12():
    return random.randint(1, 12)

def roll_d20():
    return random.randint(1, 20)

# it takes a dice expression like "2d6+3" and returns the result of the roll
# Return -> Rolls: [4, 6], Total: 13
# Rolls for narration and total for calculations
def roll_dice(expr: str):
    # Also black magic :-)
    match = re.match(r"(\d+)d(\d+)([+-]\d+)?", expr.replace(" ", ""))
    if not match:
        return 0
    #         V  <- group 1 is the number of dice, group 2 is the die type, group 3 is the modifier (if any)
    n =   int(match.group(1))
    die = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0

    rolls = [random.randint(1, die) for _ in range(n)]  # Roll the dice
    total = sum(rolls) + mod

    return total, rolls


# Stat modifier calculation (D&D style)
# 10 is the average, every 2 points above or below gives +1 or -1 modifier
#                                   V <- the function is expeted to return an integer
def stat_modifier(stat_value: int) -> int:
    return (stat_value - 10) // 2


def stat_scaling(skill_type, stats):
    if skill_type in ["attack"]:
        return stat_modifier(stats["STR"])
    if skill_type in ["magic"]:
        return stat_modifier(stats["INT"])
    return 0

#magic always hit, but the physical can miss based on DEX/STR stat (bows use a dex check, melee weapons use a str check)
# roll d20 + stat scaling vs 10 + enemy DEX check
def hit_check(attacker: dict, defender: dict, skill: dict = None, weapon_item: dict = None) -> bool:
    # Magic always hits
    if skill and skill["type"] in ("magic", "buff", "debuff"):
        if skill.get("effects") and any("mana_cost" in e for e in skill["effects"]):
                    mana_cost = sum(e.get("mana_cost", 0) for e in skill["effects"])
                    if attacker["mana"] < mana_cost:
                        return False  # Not enough mana
                    attacker["mana"] = update_stat(attacker["mana"], -mana_cost, 0)
        return True

    # Determine weapon type
    if weapon_item is None:
        # Fallback: find in inventory by name
        return False  # No weapon data, assume miss

    sub_type = weapon_item.get("subType", "melee")
    if sub_type == "ranged":
        attack_stat = attacker["stats"]["DEX"]
    elif sub_type == "melee":
        attack_stat = attacker["stats"]["STR"]
    else:
        attack_stat = attacker["stats"]["STR"]

    attack_roll = roll_d20() + stat_modifier(attack_stat)
    defense_roll = 10 + stat_modifier(defender["stats"]["DEX"])
    return attack_roll >= defense_roll


def skill_damage(skill, character):
    total = 0
    all_rolls = []

    for effect in skill.get("effects", []):
        if effect["kind"] == "damage":
            dmg_total, rolls = roll_dice(effect["value"])
            all_rolls.extend(rolls)
            total += dmg_total

    scaling = stat_scaling(skill["type"], character["stats"])
    total += scaling

    return {"total": max(0, total), "rolls": all_rolls, "scaling": scaling}

def skill_buff(skill, character):
    total = 0
    all_rolls = []
    duration = 0

    for effect in skill.get("effects", []):
        if effect["kind"] == "buff":
            buff_total, rolls = roll_dice(effect["value"])
            all_rolls.extend(rolls)
            total += buff_total
            if "duration" in effect:
                duration, _ = roll_dice(effect["duration"])

    return {"total": total, "rolls": all_rolls, "duration": duration}


def skill_debuff(skill, character):
    total = 0
    all_rolls = []
    duration = 0

    for effect in skill.get("effects", []):
        if effect["kind"] == "debuff":
            debuff_total, rolls = roll_dice(effect["value"])
            all_rolls.extend(rolls)
            total += debuff_total
            if "duration" in effect:
                duration, _ = roll_dice(effect["duration"])

    return {"total": total, "rolls": all_rolls, "duration": duration}


def weapon_base_damage(weapon_item: dict) -> int:
    total = 0
    all_rolls = []

    for effect in weapon_item.get("effects", []):
        if effect["kind"] == "damage":
            dmg, rolls = roll_dice(effect["value"])
            total += dmg
            all_rolls.extend(rolls)

    return {"total": total, "rolls": all_rolls}


# Decide who starts combat using DEX.
def determine_initiative(player: dict, enemy: dict):
    while True:
        player_roll = roll_d20() + stat_modifier(player["stats"]["DEX"])
        enemy_roll  = roll_d20() + stat_modifier(enemy["stats"]["DEX"])

        print(f"[INITIATIVE] {player['name']} rolls {player_roll} | {enemy['name']} rolls {enemy_roll}")

        if player_roll > enemy_roll:
            return [player, enemy]
        elif enemy_roll > player_roll:
            return [enemy, player]
        else:
            print("[INITIATIVE] Tie! Rerolling...")


# Perform an attack (weapon or skill) and return combat result.
def combat_attack(attacker, defender, skill=None, weapon_item=None):
    result_data = {"result": "miss", "damage": 0, "defender_hp": defender.get("current_hp", 0), "skill_rolls": [], "weapon_rolls": []}
    
    if not hit_check(attacker, defender, skill, weapon_item):
        return result_data

    total_damage = 0

    # Skill
    if skill:
        dmg = skill_damage(skill, attacker)
        total_damage += dmg["total"]
        result_data["skill_rolls"] = dmg["rolls"]

    # Weapon
    if weapon_item and (skill is None or skill["type"] == "attack"):
        dmg = weapon_base_damage(weapon_item)
        total_damage += dmg["total"]
        result_data["weapon_rolls"] = dmg["rolls"]

    defender["current_hp"] = update_stat(defender.get("current_hp", 0), -total_damage, 0, defender["max_hp"])
    result_data["damage"] = total_damage
    result_data["defender_hp"] = defender["current_hp"]
    result_data["result"] = "hit"

    return result_data





# Determine the type of skill and call the appropriate function.
def resolve_skill(skill, character):
    if skill["type"] == "attack":
        return skill_damage(skill, character)
    elif skill["type"] == "buff":
        return skill_buff(skill, character)
    elif skill["type"] == "debuff":
        return skill_debuff(skill, character)
    else:
        return {"total": 0, "rolls": [], "duration": 0}


# MAke so that if the item is a weapon it changes the equipped weapon
def use_item(character, real_name, items):
    real_name = real_name.strip().lower()
    inventory_map = {i.lower(): i for i in character["inventory"]}

    if real_name not in inventory_map:
        return False, "Item not found"

    real_name = inventory_map[real_name]
    item = next((i for i in items if i["name"] == real_name), None)
    if not item:
        return False, "Invalid item"

    # Equip weapon/magical
    if item["itemType"] in ("weapon", "magical"):
        character["equipped_weapon"] = item["name"]
        return True, f"You equip the {item['name']}."

    # Healing or fixed effect
    for effect in item.get("effects", []):
        if effect["kind"] == "heal":
            value = str(effect["value"]).strip()

            # Detect dice expression like 3d6+2
            dice_pattern = r"^\d+d\d+([+-]\d+)?$"
            if re.match(dice_pattern, value):
                heal, rolls = roll_dice(value)
                character["current_hp"] = update_stat(character["current_hp"], heal, 0, character["max_hp"])
                return True, f"You heal for {heal} HP (rolls: {rolls})"
            else:
                # Treat as fixed number
                try:
                    heal = int(value)
                except:
                    heal = 0
                character["current_hp"] = update_stat(character["current_hp"], heal, 0, character["max_hp"])
                return True, f"You heal for {heal} HP."

    # Handle consumable uses
    if "uses" in item and item["uses"] > 0:
        item["uses"] -= 1
        if item["uses"] == 0:
            character["inventory"].remove(real_name)
        return True, f"Used {real_name}, {item['uses']} uses left"

    # Default: remove consumable
    character["inventory"].remove(real_name)
    return True, f"Used {real_name}"






# Parse free-text player input using AI and return one of the four actions
def get_action_from_ai(user_input: str, character: dict) -> str:
    """
    Intelligent action parser that:
    1. Analyzes user input
    2. Checks against character's actual skills/items
    3. Returns the best matching action with specific item/skill
    """
    print(f"\n[AI Parser] Analyzing: '{user_input}'")
    
    # Get character's actual skills and items
    character_skills = character.get("skills", [])
    character_items = character.get("inventory", [])
    
    # Find available skills from database
    available_skills = []
    for skill_name in character_skills:
        skill = get_skill_by_name(skill_name, SKILLS_DB)
        if skill:
            available_skills.append(skill)
    
    # Find available items from database
    available_items = []
    for item_name in character_items:
        item = get_item_by_name(item_name, ITEMS_DB)
        if item:
            available_items.append(item)
    
    print(f"[AI Parser] Character has {len(available_skills)} skills: {[s['name'] for s in available_skills]}")
    print(f"[AI Parser] Character has {len(available_items)} items: {[i['name'] for i in available_items]}")
    
    # Check if input matches any skill
    if available_skills:
        # Find the most similar skill to user input
        best_skill, skill_similarity = find_most_similar_item(user_input, available_skills)
        print(f"[AI Parser] Best skill match: '{best_skill['name']}' (similarity: {skill_similarity:.2f})")
        
        if skill_similarity > 0.3:  # Good enough match
            print(f"[AI Parser] Returning 'use skill' with skill: {best_skill['name']}")
            # Store the selected skill in a global or return it somehow
            # For now, we'll modify the character to track selected skill
            character["_selected_skill"] = best_skill["name"]
            return "use skill"
    
    # Check if input matches any item
    if available_items:
        best_item, item_similarity = find_most_similar_item(user_input, available_items)
        print(f"[AI Parser] Best item match: '{best_item['name']}' (similarity: {item_similarity:.2f})")
        
        if item_similarity > 0.3:
            print(f"[AI Parser] Returning 'use item' with item: {best_item['name']}")
            character["_selected_item"] = best_item["name"]
            return "use item"
    
    # Check for attack keywords
    attack_keywords = ["attack", "hit", "strike", "slash", "shoot", "swing", "bash", "bow", "sword", "arrow", "melee"]
    user_input_lower = user_input.lower()
    for keyword in attack_keywords:
        if keyword in user_input_lower:
            print(f"[AI Parser] Detected attack keyword: '{keyword}'")
            return "attack"
    
    # Check for run keywords
    run_keywords = ["run", "flee", "escape", "retreat", "withdraw", "leave"]
    for keyword in run_keywords:
        if keyword in user_input_lower:
            print(f"[AI Parser] Detected run keyword: '{keyword}'")
            return "run"
    
    # Fallback: Ask AI to decide
    print("[AI Parser] Using AI to decide action...")
    
    # Prepare skill and item info for the AI
    skill_info = ""
    if available_skills:
        skill_info = "Available skills: " + ", ".join([f"{s['name']} ({s['type']})" for s in available_skills])
    
    item_info = ""
    if available_items:
        item_info = "Available items: " + ", ".join([f"{i['name']} ({i['itemType']})" for i in available_items])
    
    prompt = [
        {
            "role": "system",
            "content": f"""You are a combat action parser. Analyze the player's input and decide the best action.
Character has: {skill_info} {item_info}
Possible actions: attack, use skill, use item, run

Return JSON with:
- action: one of "attack", "use skill", "use item", "run"
- target_skill: (if action is "use skill") the skill name from available skills
- target_item: (if action is "use item") the item name from available items
- confidence: 0.0 to 1.0 how confident you are

Example: {{"action": "use skill", "target_skill": "Fire Bolt", "confidence": 0.8}}"""
        },
        {"role": "user", "content": f"Player says: '{user_input}'"}
    ]
    
    try:
        raw = narrate(prompt)
        parsed = extract_json(raw)
        action = parsed.get("action", "attack").lower()
        
        # Store selected skill/item if provided by AI
        if action == "use skill" and "target_skill" in parsed:
            character["_selected_skill"] = parsed["target_skill"]
            print(f"[AI Parser] AI selected skill: {parsed['target_skill']}")
        elif action == "use item" and "target_item" in parsed:
            character["_selected_item"] = parsed["target_item"]
            print(f"[AI Parser] AI selected item: {parsed['target_item']}")
        
        confidence = parsed.get("confidence", 0.5)
        print(f"[AI Parser] AI decided: {action} (confidence: {confidence})")
        
        return action
    except Exception as e:
        print(f"[AI Parser Error] {e}. Defaulting to attack.")
        return "attack"




#! in the actual database comabt loop substitute all the reference 
#! to the items_db with a query to the database
def get_item_by_name(name: str, items_db: list):
    return next((i for i in items_db if i["name"] == name), None)

def get_skill_by_name(name: str, skills_db: list):
    return next((s for s in skills_db if s["name"] == name), None)

with open(skill_path, "r", encoding="utf-8") as f:
    SKILLS_DB = json.load(f)

with open(item_path, "r", encoding="utf-8") as f:
    ITEMS_DB = json.load(f)

try:
    with open(enemy_path, "r", encoding="utf-8") as f:
        enemies_data = json.load(f)
    
    # Ensure ENEMIES_DB is always a list
    if isinstance(enemies_data, dict):
        # If single enemy object, wrap in list
        ENEMIES_DB = [enemies_data]
    elif isinstance(enemies_data, list):
        ENEMIES_DB = enemies_data
    else:
        print(f"[ERROR] Invalid enemies.json format. Expected dict or list, got {type(enemies_data)}")
        ENEMIES_DB = []
except Exception as e:
    print(f"[ERROR] Failed to load enemies.json: {e}")
    ENEMIES_DB = []





def combat_loop(player, enemies, items, state, mode="manual", similarity_threshold=0.3):
    print(f"\n[COMBAT START] You encounter {len(enemies)} enemies!")
    for i, enemy in enumerate(enemies):
        print(f"  {i+1}. {enemy['name']} (Level {enemy['level']}, HP: {enemy['current_hp']}/{enemy['max_hp']})")
    
    # Track which enemies are alive
    alive_enemies = enemies.copy()
    current_enemy_index = 0
    
    combat_history = []

    while player["current_hp"] > 0 and alive_enemies:
        # Get current enemy to fight
        current_enemy = alive_enemies[current_enemy_index]
        
        print(f"\n[Status] {player['name']} HP: {player['current_hp']}/{player['max_hp']}, Mana: {player['mana']}")
        print(f"Alive enemies: {len(alive_enemies)}")
        for i, enemy in enumerate(alive_enemies):
            marker = ">" if i == current_enemy_index else " "
            print(f"  {marker} {i+1}. {enemy['name']} - HP: {enemy['current_hp']}/{enemy['max_hp']}")

        #! ================= PLAYER TURN =================
        user_input = input("\nDescribe your action (or 'target X' to switch enemy): ").strip()
        
        # Check if player wants to switch target
        if user_input.lower().startswith("target "):
            try:
                target_num = int(user_input.split()[1])
                if 1 <= target_num <= len(alive_enemies):
                    current_enemy_index = target_num - 1
                    print(f"Switched target to {alive_enemies[current_enemy_index]['name']}")
                    continue
                else:
                    print(f"Invalid target number. Choose 1-{len(alive_enemies)}")
                    continue
            except (ValueError, IndexError):
                print("Usage: 'target X' where X is enemy number")
                continue
        
        # Parse player action with intelligent AI
        action = get_action_from_ai(user_input, player)
        
        # Clear previous selections
        selected_skill = player.pop("_selected_skill", None)
        selected_item = player.pop("_selected_item", None)
        
        # Execute player action
        combat_text = ""
        
        if action == "attack":
            weapon_item = get_item_by_name(player["equipped_weapon"], items)
            result = combat_attack(player, current_enemy, weapon_item=weapon_item)
            rolls = result["weapon_rolls"] or []
            combat_text = f"You attack {current_enemy['name']} with {player['equipped_weapon']} for {result['damage']} damage."
            if rolls:
                combat_text += f" Rolls: {rolls}"
            
            # Check if enemy died
            if current_enemy["current_hp"] <= 0:
                combat_text += f"\n{current_enemy['name']} has been defeated!"
                alive_enemies.pop(current_enemy_index)
                if current_enemy_index >= len(alive_enemies) and alive_enemies:
                    current_enemy_index = len(alive_enemies) - 1

        elif action == "use skill":
            # Use the skill selected by the AI parser
            if selected_skill:
                skill = get_skill_by_name(selected_skill, SKILLS_DB)
                if skill:
                    # Check if player has enough mana
                    mana_cost = 0
                    if skill.get("effects"):
                        for effect in skill["effects"]:
                            mana_cost += effect.get("mana_cost", 0)
                    
                    if mana_cost > 0 and player.get("mana", 0) < mana_cost:
                        combat_text = f"You try to cast {skill['name']} but don't have enough mana! (Need: {mana_cost}, Have: {player.get('mana', 0)})"
                    else:
                        # For magic skills, create dummy weapon item
                        weapon_item = None
                        if skill["type"] in ("magic", "buff", "debuff"):
                            weapon_item = {"subType": "melee"}
                        
                        result = combat_attack(player, current_enemy, skill=skill, weapon_item=weapon_item)
                        rolls = result["skill_rolls"] or []
                        
                        combat_text = f"You cast {skill['name']} on {current_enemy['name']} for {result['damage']} damage."
                        if rolls:
                            combat_text += f" Rolls: {rolls}"
                        
                        if mana_cost > 0:
                            combat_text += f" (Mana cost: {mana_cost})"
                        
                        # Check if enemy died
                        if current_enemy["current_hp"] <= 0:
                            combat_text += f"\n{current_enemy['name']} has been defeated!"
                            alive_enemies.pop(current_enemy_index)
                            if current_enemy_index >= len(alive_enemies) and alive_enemies:
                                current_enemy_index = len(alive_enemies) - 1
                else:
                    combat_text = f"Skill '{selected_skill}' not found!"
            else:
                # Try to use first skill if none selected
                if player.get("skills"):
                    skill_name = player["skills"][0]
                    skill = get_skill_by_name(skill_name, SKILLS_DB)
                    if skill:
                        player["_selected_skill"] = skill["name"]
                        # Recursively try again
                        continue
                    else:
                        combat_text = "You don't have any usable skills!"
                else:
                    combat_text = "You don't have any skills!"

        elif action == "use item":
            if selected_item:
                success, msg = use_item(player, selected_item, items)
                combat_text = msg
                if not success:
                    combat_text = f"Failed to use {selected_item}."
            else:
                # Try to use first item if none selected
                if player.get("inventory"):
                    item_name = player["inventory"][0]
                    player["_selected_item"] = item_name
                    # Recursively try again
                    continue
                else:
                    combat_text = "You don't have any items!"

        elif action == "run":
            roll = roll_d20() + stat_modifier(player["stats"]["DEX"])
            if roll >= 15:
                print("You successfully escape from combat!")
                return False
            else:
                combat_text = "You try to run but fail to escape!"

        else:
            combat_text = f"{player['name']} hesitates, unsure what to do."

        #! ================= ENEMY TURNS =================
        enemy_actions = []
        
        # All alive enemies get a turn
        for i, enemy in enumerate(alive_enemies):
            if enemy["current_hp"] <= 0:
                continue
                
            action_type, action_data = enemy_choose_action(enemy, player)
            result = execute_enemy_action(enemy, player, action_type, action_data)
            
            enemy_actions.append({
                "enemy": enemy,
                "result": result,
                "index": i
            })
        
        # Combine enemy actions into one text
        if enemy_actions:
            enemy_texts = []
            for action in enemy_actions:
                enemy = action["enemy"]
                result = action["result"]
                enemy_texts.append(f"{enemy['name']}: {result['message']}")
            
            if combat_text:
                combat_text += "\n" + "\n".join(enemy_texts)
            else:
                combat_text = "\n".join(enemy_texts)
        
        # Check if player died
        if player["current_hp"] <= 0:
            combat_text += "\nYou have been knocked unconscious!"
        
        #! ================= AI NARRATION =================
        history = [
            system_rules,
            {"role": "system", "content": f"Current location: {state['location']}."},
            {"role": "system", "content": f"Player: {player['name']} HP {player['current_hp']}/{player['max_hp']}."},
            {"role": "system", "content": f"Alive enemies: {len(alive_enemies)}."},
            {"role": "user", "content": f"Combat log:\n{combat_text}\nNarrate faithfully without inventing actions."}
        ]

        ai_output = narrate(history)
        try:
            narration = extract_json(ai_output).get("narration", combat_text)
        except:
            narration = combat_text

        print("\n" + narration)
        combat_history.append(narration)
        
        # If player died, end combat
        if player["current_hp"] <= 0:
            break

    #! ================= COMBAT END =================
    if player["current_hp"] <= 0:
        print("\nYou have been defeated...")
        return False
    
    print(f"\nYou defeated all enemies!")
    
    # Grant XP for all defeated enemies
    total_xp = 0
    for enemy in enemies:
        if enemy["current_hp"] <= 0:
            xp_reward = enemy.get("cr", 1) * 10
            total_xp += xp_reward
    
    player["xp"] = update_stat(player["xp"], total_xp)
    print(f"You gain {total_xp} XP!")
    
    # Level up check
    if player["xp"] >= player["level"] * 100:
        player["level"] += 1
        player["max_hp"] += 10
        player["current_hp"] = player["max_hp"]
        player["mana"] += 10
        print(f"\n[LEVEL UP] You are now level {player['level']}! Max HP increased to {player['max_hp']}.")
    
    return True






# Spawn an enemy based on level budget system
# Returns a copy of an enemy template with randomized HP
def spawn_enemy(location_type="wilderness", player_level=1):
    # Get all enemies at or below player level
    all_enemies = ENEMIES_DB.copy()
    
    if not all_enemies:
        print("[ERROR] No enemies loaded from enemies.json")
        return []
    
    # Decide: multiple weak enemies or single stronger enemy?
    choice = random.random()
    
    if choice < 0.5 and player_level >= 2:
        # Spawn multiple weak enemies (e.g., 2 level 1 goblins)
        num_enemies = random.randint(2, min(3, player_level))
        weak_enemies = [e for e in all_enemies if e["level"] == 1]
        
        if not weak_enemies:
            weak_enemies = [e for e in all_enemies if e["level"] <= player_level]
        
        spawned_enemies = []
        for _ in range(num_enemies):
            enemy_template = random.choice(weak_enemies)
            enemy = enemy_template.copy()
            
            # Randomize HP - handle both old and new JSON formats
            if "max_hp" in enemy:
                if isinstance(enemy["max_hp"], dict):
                    # New format: {"min": X, "max": Y}
                    min_hp = enemy["max_hp"]["min"]
                    max_hp = enemy["max_hp"]["max"]
                    enemy["current_hp"] = random.randint(min_hp, max_hp)
                    enemy["max_hp"] = enemy["current_hp"]
                else:
                    # Old format: just a number
                    enemy["current_hp"] = enemy["max_hp"]
            
            spawned_enemies.append(enemy)
        
        return spawned_enemies
    else:
        # Spawn single enemy at player's level or slightly below
        max_enemy_level = min(player_level, 10)
        possible_enemies = [e for e in all_enemies if e["level"] <= max_enemy_level]
        
        if not possible_enemies:
            possible_enemies = [e for e in all_enemies if e["level"] == 1]
        
        enemy_template = random.choice(possible_enemies)
        enemy = enemy_template.copy()
        
        # Randomize HP - handle both old and new JSON formats
        if "max_hp" in enemy:
            if isinstance(enemy["max_hp"], dict):
                # New format: {"min": X, "max": Y}
                min_hp = enemy["max_hp"]["min"]
                max_hp = enemy["max_hp"]["max"]
                enemy["current_hp"] = random.randint(min_hp, max_hp)
                enemy["max_hp"] = enemy["current_hp"]
            else:
                # Old format: just a number
                enemy["current_hp"] = enemy["max_hp"]
        
        return [enemy]  # Return as list for consistency

# Simple AI for enemy to choose an action
# Returns: ("attack", attack_index) or ("skill", skill_name) or ("item", item_name)
def enemy_choose_action(enemy, player):
    if "attacks" not in enemy or not enemy["attacks"]:
        return ("attack", 0)  # Fallback
    
    available_attacks = enemy["attacks"]
    
    # Simple random selection from all available attacks
    attack_index = random.randint(0, len(available_attacks) - 1)
    return ("attack", attack_index)


#Execute the chosen enemy action
def execute_enemy_action(enemy, player, action_type, action_data):
    if action_type == "attack":
        attack_index = action_data
        if attack_index < len(enemy.get("attacks", [])):
            attack = enemy["attacks"][attack_index]
            
            # Prepare attack data structure
            attack_data = {
                "type": "attack",
                "effects": attack["effects"]
            }
            
            # Get weapon type from attack's subType field
            weapon_item = {"subType": attack.get("subType", "melee")}
            
            # Use the proper hit_check function
            hits = hit_check(enemy, player, skill=attack_data, weapon_item=weapon_item)
            
            if hits:
                # Calculate damage using the proper dice roll
                damage_result = roll_dice(attack["effects"][0]["value"])
                if isinstance(damage_result, tuple):
                    damage = damage_result[0]
                    rolls = damage_result[1]
                else:
                    damage = damage_result
                    rolls = []
                
                # Apply appropriate stat scaling for damage
                if weapon_item["subType"] == "ranged":
                    stat_bonus = stat_modifier(enemy["stats"]["DEX"])
                else:
                    stat_bonus = stat_modifier(enemy["stats"]["STR"])
                
                total_damage = max(0, damage + stat_bonus)
                
                # Apply damage to player
                player["current_hp"] = update_stat(player["current_hp"], -total_damage, 0, player["max_hp"])
                
                # Get the roll details for narration
                rolls_text = f" Rolls: {rolls}" if rolls else ""
                stat_text = f" (+{stat_bonus} from stats)" if stat_bonus > 0 else f" ({stat_bonus} from stats)" if stat_bonus < 0 else ""
                
                return {
                    "success": True,
                    "damage": total_damage,
                    "attack_name": attack["name"],
                    "rolls": rolls,
                    "stat_bonus": stat_bonus,
                    "message": f"The {enemy['name']} uses {attack['name']} for {total_damage} damage!{stat_text}{rolls_text}"
                }
            else:
                # Miss
                return {
                    "success": False,
                    "damage": 0,
                    "attack_name": attack["name"],
                    "message": f"The {enemy['name']} uses {attack['name']} but misses!"
                }

    # Fallback
    return {
        "success": False,
        "damage": 0,
        "message": f"The {enemy['name']} hesitates..."
    }





# !DEPRECTED(?)
# # the weapons are superclass of items, 
# it taskes the id, it sees into the speelname form what it can use and jump to the skill json to get the damage and other stats

# the potion are used only once then they are removed from the inventory -> imp
# nell'inventario c'è la baccheta con gli usi effetivi, poi non la puoi piu usare
# dopo 20 turni si ricarica






# ! Dice roll for the chance to encounter an enemy (cr4 and 2cr3 enemies like dnd) when entering a dungeon
# ! The dungeon is generated by an algorithm I will stole from GitHub
# TODO implement the level up system based on XP gained -> the cap to reach the next level increases by a factor of 2 every 10 levels (like in dnd)


# --- Game Loop ---
def main():
    # Python has to explicitly state that we are using the global variables (the serpet is cleraly not fit to be a C competitor :-P)
    global long_term_memory
    global turn_count
    global recent_history
    global mana_regen_per_turn
    global character
    print("=== ADA TI DA' IL BENVENUTO ===")
    print("\nDescribe your character in your own words (free text):")
    user_desc = input("> ")

    character = create_character_from_description(user_desc)
    print("\nYour character has been created:")
    print(json.dumps(character, indent=2))

    state = {"location": "Taverna Iniziale", 
             "quest": "Nessuna"
    }

    # Choose combat mode
    print("\nChoose combat mode:")
    print("1. Manual (you select actions)")
    print("2. AI Narration (you narrate, AI decides actions)")
    mode_choice = input("> ").strip()
    if mode_choice == "2":
        combat_mode = "ai"
    else:
        combat_mode = "manual"

    print(f"\n[INFO] Combat mode set to: {combat_mode}")

    # Combat encounter chance variables
    last_combat_turn = 0
    combat_cooldown = 30  # Minimum turns between combats

    while True:
        user_input = input("\n What do you do? (type 'quit' to quit) \n> ")
        
        if user_input.lower() in ["exit", "quit", "esci"]:
            print("Saving game (lie), Goodbye!")
            break

        recent_history.append({"role": "user", "content": user_input})

        # Refresh history with the latest recent_history every turn (with every enter command)
        history = [
            system_rules,
            alignment_prompt,
            {"role": "system", "content": f"Long-term memory: {long_term_memory}"},
            {"role": "system", "content": f"Character sheet: {character}"},
            {"role": "system", "content": f"State: {state}"},
            {"role": "system", "content": f"The character's alignment is {character['alignment_righteousness']} {character['alignment_morality']}."}
        ] + recent_history[-10:]  # last 10 messages (5 ai + 5 user = 5 completed turns) for context

        output = narrate(history)

        try:
            data = extract_json(output)
            recent_history.append({"role": "assistant", "content": data["narration"]})
            turn_count += 1

            #! ================= RANDOM ENCOUNTER LOGIC =================
            if (turn_count - last_combat_turn > combat_cooldown and 
                random.random() < 0.2 and  # 20% chance per turn
                state["location"].lower() not in ["tavern", "town", "city", "shop", "taverna iniziale", "inn"]):
                
                print("\n[ALERT] You are ambushed by enemies!")
                enemies = spawn_enemy(state["location"].lower(), character["level"])
                victory = combat_loop(character, enemies, ITEMS_DB, state, mode=combat_mode)
                
                if victory:
                    last_combat_turn = turn_count
                    print("\n[SYSTEM] After the battle, you continue your journey...")
                    # Give the player a moment before continuing
                    input("Press Enter to continue...")
                else:
                    print("\nGame Over!")
                    break
            
            #! ================= FORCED ENCOUNTER FROM AI =================
            elif data.get("encounter"):
                print("\n[ALERT] Combat has started!")
                enemies = spawn_enemy(state["location"].lower(), character["level"])
                
                if not enemies:
                    print("[ERROR] No enemies could be spawned. Continuing adventure...")
                    continue  # Skip combat if no enemies
                
                victory = combat_loop(character, enemies, ITEMS_DB, state, mode=combat_mode)
                
                if victory:
                    last_combat_turn = turn_count
                    print("\n[SYSTEM] After the battle, you continue your journey...")
                    input("Press Enter to continue...")
                else:
                    print("\nGame Over! \nIt was indeed dangerous to go alone, Zelda...")
                    break
            
            #! ================= NORMAL TURN PROCESSING =================
            # Add/remove items from inventory
            for item in data.get("found_items", []):
                if item not in character["inventory"]:
                    character["inventory"].append(item)

            for item in data.get("lost_items", []):
                if item in character["inventory"]:
                    character["inventory"].remove(item)

            # Update stats
            character["max_hp"] = update_stat(character["max_hp"], data.get("max_hp_change", 0), 0, 100)
            character["gold"] = update_stat(character["gold"], data.get("gold_change", 0))
            character["xp"] = update_stat(character["xp"], data.get("xp_gained", 0))

            # Reduce mana if AI specifies a mana cost
            if "mana_change" in data:
                character["mana"] = update_stat(character["mana"], data["mana_change"], 0)
            elif turn_count % 5 == 0:
                # Passive mana regen every 5 turns
                character["mana"] = update_stat(character["mana"], mana_regen_per_turn, 0)

            # Update the location and current quest
            if "location" in data:
                state["location"] = data["location"]
            if "quest" in data:
                state["quest"] = data["quest"]

            # Print status for debugging
            print("-" * 40)
            print(f"[Location: {state['location'].upper()}]")
            print(f"[Quest: {state['quest']}]")
            print(f"[Level: {character['level']} | XP: {character['xp']}/{(character['level'] + 1) * 100}]")
            print(f"[HP: {character['current_hp']}/{character['max_hp']} | Mana: {character['mana']} | Gold: {character['gold']}]")
            print("-" * 40)

            # Print the narration
            print(f"\n{data['narration']}")

            # Every 10 messages (5 turns), summarise and update long-term memory
            if turn_count > 0 and turn_count % 10 == 0:
                print("\n[SYSTEM] Ada is sorting through her memories...")
                long_term_memory = summarise_memory(long_term_memory, recent_history)
                print(f"[Memory Updated]: {long_term_memory[:100]}...")

        except Exception as e:
            print(f"\n[NARRATOR ERROR] The master is confused: {e}")
            print(f"Raw response: {output}")

if __name__ == "__main__":
    main()




# # Track encountered NPCs --> talk to other members of the group about this feature
#This shoud be taken from the database in a real implementation 
# (the named npc are remembered in the databse with their starting location and other info)
# if "encounter_npc" in data:
#     npc_name = data["encounter_npc"]
#     if npc_name not in encountered_npcs:
#         encountered_npcs.add(npc_name)
#         print(f"[SYSTEM] You have encountered a new NPC: {npc_name}")