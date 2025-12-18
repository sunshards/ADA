import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from src.brain import load_character

load_dotenv()

example_character_id = ObjectId("6943f1e9b2b9aad9d81bb75f")

# Test function to verify MongoDB connection and character loading
def test_load():
    # 1. Setup the Flask app shell to provide current_app.db
    app = Flask(__name__)
    
    # 2. Connect to the EXACT database name used in __init__.py
    connection_string = os.getenv("CONNECTION_STRING")
    client = MongoClient(connection_string)
    app.db = client["ADADatabase"] # Must match __init__.py

    with app.app_context():
        # The ID from your prompt
        target_id = "6943f1e9b2b9aad9d81bb75f"
        
        collections = app.db.list_collection_names()
        print(f"MongoDB works! Collections: {collections}")

        print(f"--- Searching in {app.db.name}.Users ---")
        character = load_character(target_id)
        
        if character:
            print(f"[SUCCESS] Loaded Character: {character.get('name')}")
            print(f"id: {character.get('_id')} ")
            print(f"Stats: {character.get('stats')}")
            print(f"Inventory: {character.get('inventory')}")
        else:
            # Debugging the document structure
            raw_user = app.db['Users'].find_one({"_id": ObjectId(target_id)})
            if raw_user:
                print("[STRUCTURE ERROR] User found, but 'Characters' array is missing or empty.")
                print(f"Keys found in document: {list(raw_user.keys())}")
            else:
                print("[NOT FOUND] No document exists with that ObjectId in 'ADADatabase.Users'.")

if __name__ == "__main__":
    test_load()