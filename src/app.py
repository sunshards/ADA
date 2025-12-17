from openai import OpenAI
from dotenv import load_dotenv
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import time
import re
import json

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

class Statistic(Enum):
    STR = "strength"
    CON = "constitution"
    DEX = "dexterity"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"



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



# ! Dice roll for the chance to encounter an enemy (cr4 and 2cr3 enemies like dnd) when entering a dungeon
# ! The dungeon is generated by an algorithm I will stole from GitHub

# Inspiration: Claude playing Pokémon (too complicated to implement here)
# from point to maxthokens (point2) -> summary1 
# from point2 to maxthokens (point3) -> summary2
# Context saved: summary1 + summary2 + recent messages (?)


# Summarises the long-term memory by extracting the most important events from recent history
# Updates the memory so the AI can maintain context without exceeding token limits
# Returns a concise summary of the adventure to be used in future turns
def summarise_memory(long_memory, recent_history):
    messages = [
            {"role": "system", "content": "You are a reporter. Summarise the salient facts of the adventure."},
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
    prompt = [
            {"role": "system", "content": "You are a character creation AI. Generate a complete D&D-style character sheet in JSON format."},
            {"role": "user", "content": f"""
        Create a character sheet based on this description:
        {description}

        Include the following fields:
        - name
        - race
        - class
        - max_hp
        - gold
        - xp
        - level
        - mana
        - inventory
        - equipped_weapon
        - alignment_righteousness
        - alignment_morality
        - birthplace
        - skills (its an empty list)
        - description
        - stats (STR, CON, DEX, INT, WIS, CHA)

        Constraints for stats:
        - Each individual stat must be at least 5.
        - The sum of all stats must **not exceed 45**.
        - Distribute stats logically based on the character description.
        - Keep stats as integers.

        Return **only valid JSON**, without explanations or markdown. Ensure the JSON is complete and all fields are present.
        """}
        ] 

    output = narrate(prompt)
    try:
        character = extract_json(output)
        # If equipped_weapon is not present in the weapon list, find the most similar one.
        #                                       V <- this is the name of a element of the list: used in the loop to create a list of weapon names
        if character["equipped_weapon"] not in [w["name"] for w in weapons]:
            result = find_most_similar_item(character["equipped_weapon"], weapons)
            most_similar = result[0]  # <-- Dictionary of the most similar weapon
            similarity = result[1]    # <-- Similarity score (not used here, but could be logged) #! TBH: we have to decide if we use it or not (could be used to invent the weapon if the similarity is too low)
            character["equipped_weapon"] = most_similar["name"]
            if most_similar["name"] not in character["inventory"]:
                character["inventory"].append(most_similar["name"])

        return character
    except Exception as e:
        print(f"[ERROR] Failed to generate character: {e}")
        print("Using placeholder character instead.")
        # Fallback placeholder
        return {
            "name": "Unknown Hero",
            "race": "Human",
            "class": "Adventurer",
            "max_hp": 100,
            "gold": 50,
            "xp": 0,
            "level": 1,
            "mana": 50,
            "inventory": ["short sword"],
            "equipped_weapon": "short sword",
            "alignment_righteousness": "neutral",
            "alignment_morality": "neutral",
            "birthplace": "",
            "description": description,
            "skills": [],
            "stats": {
                Statistic.STR.value: 5,
                Statistic.CON.value: 5,
                Statistic.DEX.value: 5,
                Statistic.INT.value: 5,
                Statistic.WIS.value: 5,
                Statistic.CHA.value: 5
            }
        }

#! Remember to do: uv add sklearn-env

# Finds the most similar item based on description using TF-IDF and cosine similarity
# Tutorial used: (https://www.newscatcherapi.com/blog-posts/ultimate-guide-to-text-similarity-with-python)
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

# Example of predefined weapons (obviusly this should be taken from the database)
weapons = [
    {"name": "Longbow", "description": "Standard bow for archers, deals 2-6 physical damage"},
    {"name": "Short Sword", "description": "Light sword, suitable for close combat"},
    {"name": "Magic Wand", "description": "Wand for casting basic spells, deals magic damage"}
]



# --- Game Loop ---
def main():
    # Python has to explicitly state that we are using the global variables (the serpet is cleraly not fit to be a C competitor :-P)
    global long_term_memory
    global turn_count
    global recent_history
    global mana_regen_per_turn
    print("=== ADA TI DA' IL BENVENUTO ===")
    print("\nDescribe your character in your own words (free text):")
    user_desc = input("> ")

    character = create_character_from_description(user_desc)
    print("\nYour character has been created:")
    print(json.dumps(character, indent=2))

    state = {"location": "Taverna Iniziale", 
             "quest": "Nessuna"
    }

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
            
            # Add/remove items from inventory
            for item in data.get("found_items", []):
                if item not in character["inventory"]:
                    character["inventory"].append(item)

            for item in data["lost_items"]:
                if item in character["inventory"]:
                    character["inventory"].remove(item)

            # Update stats                                                                      V <- default value, if the Ai forgets to include gold_change 
            character["max_hp"] = update_stat(character["max_hp"],    data.get("max_hp_change", 0), 0, 100)
            character["gold"]   = update_stat(character["gold"],      data.get("gold_change",   0))
            character["xp"]     = update_stat(character["xp"],        data.get("xp_gained",     0))


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

            # # Track encountered NPCs --> talk to other memebers of the group about this feature
            #This shoud be taken from the database in a real implementation 
            # (the named npc are remembered in the databse with their starting location and other info)
            # if "encounter_npc" in data:
            #     npc_name = data["encounter_npc"]
            #     if npc_name not in encountered_npcs:
            #         encountered_npcs.add(npc_name)
            #         print(f"[SYSTEM] You have encountered a new NPC: {npc_name}")

            # Print status for debugging
            print("-" * 30)
            print(f"[Location: {state['location'].upper()}] | Quest: {state['quest'].lower()} | HP: {character['max_hp']} | Mana: {character['mana']} | Gold: {character['gold']}")
            print("-" * 30)

            # Print the narration
            print(data["narration"])

            # Every 10 messages (5 turns), summarise and update long-term memory
            if turn_count > 0 and turn_count % 10 == 0:
                print("\n[SYSTEM] Ada is sorting through her memories...")
                long_term_memory = summarise_memory(long_term_memory, recent_history)

        except Exception as e:
            print(f"\n[NARRATOR ERROR] The master in confused: {e}")
            print(f"Raw response: {output}")

        

if __name__ == "__main__":
    main()
