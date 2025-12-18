import os
import random
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

from src.brain import load_character, save_character

load_dotenv()

# Command to run this test file directly:
# python -m src.test_db

def test_load_and_save():
    # 1. Setup the Flask app shell to provide current_app.db
    app = Flask(__name__)
    
    # 2. Connect to the EXACT database name used in __init__.py
    connection_string = os.getenv("CONNECTION_STRING")
    client = MongoClient(connection_string)
    app.db = client["ADADatabase"] 

    with app.app_context():
        target_id = "6943f1e9b2b9aad9d81bb75f"
        
        print(f"--- Testing Load for ID: {target_id} ---")
        character = load_character(target_id)
        
        if character:
            print(f"[SUCCESS] Loaded Character: {character.get('name')}")
            
            # --- START SAVE TEST ---
            original_hp = character.get('current_hp', 50)
            # Create a random value to prove the update actually happened
            new_hp_value = random.randint(1, 30) 
            
            print(f"--- Testing Save: Changing HP from {original_hp} to {new_hp_value} ---")
            character['current_hp'] = new_hp_value
            
            save_success = save_character(character)
            
            if save_success:
                # 3. Re-fetch from DB to verify it actually saved
                # We bypass load_character cache and check the collection directly
                verified_char = app.db['Characters'].find_one({"_id": ObjectId(target_id)})
                
                if verified_char and verified_char.get('current_hp') == new_hp_value:
                    print(f"[VERIFIED] Database successfully updated to {new_hp_value} HP!")
                else:
                    print("[FAILURE] Save reported success, but database value did not match!")
            else:
                print("[FAILURE] The save_character function returned False.")
            # --- END SAVE TEST ---

        else:
            # Check both collections for debugging
            raw_user = app.db['Users'].find_one({"_id": ObjectId(target_id)})
            raw_char = app.db['Characters'].find_one({"_id": ObjectId(target_id)})
            
            if raw_char:
                print(f"[HINT] Document exists in 'Characters' collection. Update load_character() to look there.")
            elif raw_user:
                print(f"[HINT] Document exists in 'Users' collection.")
            else:
                print(f"[NOT FOUND] ID {target_id} does not exist in Users or Characters.")

if __name__ == "__main__":
    test_load_and_save()