import os
import random
import time
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Import the new monolith functions
from src.brain import load_character, save_monolith_to_db, resume_adventure 

load_dotenv()

def test_monolith_flow():
    # 1. Setup the Flask app shell
    app = Flask(__name__)
    connection_string = os.getenv("CONNECTION_STRING")
    client = MongoClient(connection_string)
    app.db = client["ADADatabase"] 

    with app.app_context():
        target_id = "6943f1e9b2b9aad9d81bb75f"
        
        print(f"--- 1. Testing INITIAL LOAD ---")
        character = load_character(target_id)
        
        if not character:
            print("[FAILURE] Could not find base character. Aborting test.")
            return

        # 2. Create a Mock Monolith
        # This simulates the state during active gameplay
        monolith = {
            "character": character,
            "items_definitions": {
                "Health Potion": {"name": "Health Potion", "itemType": "consumable", "value": 10}
            },
            "long_term_memory": f"Test memory created at {time.ctime()}",
            "recent_history": [{"role": "user", "content": "Hello ADA!"}],
            "turn_count": random.randint(1, 100),
            "state": {"location": "Test Dungeon", "quest": "Verify Monolith"}
        }

        print(f"--- 2. Testing MONOLITH SAVE ---")
        # Saves to 'ResumeAdventure' collection
        save_success = save_monolith_to_db(monolith)
        
        if save_success:
            print("[SUCCESS] Monolith saved to 'ResumeAdventure' collection.")
            
            print(f"--- 3. Testing ADVENTURE RESUME ---")
            # Reconstructs the state from 'ResumeAdventure'
            resumed_monolith = resume_adventure(target_id)
            
            if resumed_monolith:
                # Verification of key data points
                check_turn = resumed_monolith.get("turn_count") == monolith["turn_count"]
                check_memory = resumed_monolith.get("long_term_memory") == monolith["long_term_memory"]
                
                if check_turn and check_memory:
                    print(f"[VERIFIED] Adventure successfully resumed at turn {resumed_monolith['turn_count']}!")
                    print(f"Memory Restored: {resumed_monolith['long_term_memory']}")
                else:
                    print("[FAILURE] Resumed data does not match saved data.")
            else:
                print("[FAILURE] resume_adventure returned None.")
        else:
            print("[FAILURE] save_monolith_to_db returned False.")

if __name__ == "__main__":
    test_monolith_flow()