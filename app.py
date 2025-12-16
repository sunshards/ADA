from openai import OpenAI
from dotenv import load_dotenv
from enum import Enum
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

        Regole:
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
"""
}


# add encountered Npc????

turn_count = 0
recent_history = []
#! Make sure to change the strat point, so you can get the places from the approved database
long_term_memory = "The character is located in the Initial Tavern. No relevant events so far."

class Statistic(Enum):
    STR = "strength"
    CON = "constitution"
    DEX = "dexterity"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"

# Shoud I use """ or # for the documentation?

# 3 tries for models distanced by a 2 second delay each one then fallback to the next one
def narrate(history, retries=3, delay=2):
    """
    Generate the narrative by trying the free models in order.
    If a model fails, try the next one.
    retries: total number of 3 attempts per model in case of rate limiting
    delay: 2 seconds to wait before retrying
    """

    for model in FREE_MODELS:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=history,
                    max_tokens=400,
                    # temperature=0.7   # Tested but not used for now
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[WARN] Model {model} failed attempt {attempt+1}: {e}")
                time.sleep(delay)
        print(f"[INFO] Passing to next model...")

    return "The narrator is temporarily out of voice. Please try again shortly."



# --- Test CLI ---
# if __name__ == "__main__":
#     print("MAIN RUNNING")

#     result = narrate(
#         character={"nome": "Arin", "classe": "Guerriero"},
#         state={"location": "Taverna Iniziale", "quest": "Nessuna"},
#         user_input="Descrivi una taverna fantasy"
#     )

#     print("RESULT:")
#     print(result)


# We cannot trust the model to always return valid JSON, so we need to extract it from the text
def extract_json(text):
    # I stole this, don't judge me. Regrex are black magic to me! :-(
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("No found JASON object in the text")
    return json.loads(match.group())



# ! Dice roll for the chance to encounter an enemy (cr4 and 2cr3 enemies like dnd) when entering a dungeon
# ! The dungeon is generated by an algorithm I will stole from GitHub


# TODO: Ensure that the state is saved. Ensure that the save is the 
# TODO: result of a prompt "Summarise the most important events" (Exampre: Claude playing Pokémon)
# TODO: implentat a function that count the max token used by the history and truncate old messages if needed 
# from point to maxthokens (point2) -> summary1 
# from point2 to maxthokens (point3) -> summary2
# Context saved: summary1 + summary2 + recent messages (?)
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


# --- Loop di gioco CLI ---
def main():
    # Python has to explicitly state that we are using the global variables (the serpet is cleraly not fit to be a C competitor :-P)
    global long_term_memory
    global turn_count
    global recent_history
    print("=== ADA TI DA' IL BENVENUTO ===")

    # Initial Character Sheet and State
    # TODO: Load the character and state from a dataabse save file if exists
    #! Class is importat in the game logic, only certain class can learn certain abylities (let it check the database for the match)
    character = {
        "name": "Monty",
        "race": "Toro Umano",
        "class": "Cs Graduate",
        "max_hp": 100,
        "gold": 50,
        "xp": 0,
        "level": 1,
        "inventory": ["spada corta"],
        "equipped_weapon": "spada corta",

        "alignment_righteousness": "neutral",
        "alignment_morality": "neutral",

        "birthplace": "",
        "description": "",

        "stats": {
            Statistic.STR.value: 14,
            Statistic.CON.value: 12,
            Statistic.DEX.value: 10,
            Statistic.INT.value: 10,
            Statistic.WIS.value: 10,
            Statistic.CHA.value: 10
        }
    }


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


            # Update the location and current quest
            if "location" in data:
                state["location"] = data["location"]
            if "quest" in data:
                state["quest"] = data["quest"]

            # Print status for debugging
            print("-" * 30)
            print(f"[Location: {state['location'].upper()}] | max_hp: {character['max_hp']} | Gold: {character['gold']}")
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
