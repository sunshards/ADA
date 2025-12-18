import os
import random
import time
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
# Import both functions for the test
from src.brain import load_character, save_character 

# Import the new monolith functions
from src.brain import load_character, save_monolith_to_db, resume_adventure 

target_id = "6943f1e9b2b9aad9d81bb75f"

def setup_test_app():
    """Helper to setup the Flask app context and DB connection."""
    app = Flask(__name__)
    connection_string = os.getenv("CONNECTION_STRING")
    client = MongoClient(connection_string)
    app.db = client["ADADatabase"] 
    return app

def test_load_and_save():
    app = setup_test_app()

    with app.app_context():
        print(f"--- Testing LOAD for ID: {target_id} ---")
        character = load_character(target_id)
        
        if not character:
            print("[FAIL] Character not found. Cannot proceed with save test.")
            return

        print(f"[SUCCESS] Loaded: {character.get('name')}")
        
        # --- TEST SAVE FUNCTION ---
        print(f"\n--- Testing SAVE for ID: {target_id} ---")
        
        # 1. Modify a value (e.g., increment gold)
        original_gold = character.get("gold", 0)
        new_gold_value = original_gold + 10
        character["gold"] = new_gold_value
        print(f"Attempting to update gold: {original_gold} -> {new_gold_value}")

        # 2. Call the save function
        save_success = save_character(character)
        
        if save_success:
            # 3. Verify by re-fetching from the DB
            updated_char = load_character(target_id)
            if updated_char.get("gold") == new_gold_value:
                print(f"[SUCCESS] Database updated! New gold: {updated_char.get('gold')}")
            else:
                print(f"[FAIL] Save returned True, but data in DB is {updated_char.get('gold')}")
        else:
            print("[FAIL] save_character function returned False.")

if __name__ == "__main__":
    test_load_and_save()
