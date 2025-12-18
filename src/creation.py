from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app
)

from . import global_config
from . import brain
from . import character
import json
import base64
import os
from PIL import Image
import io
from bson.objectid import ObjectId

bp = Blueprint('creation', __name__, url_prefix='/creation')

@bp.route('/', methods=('GET', 'POST'))
def creation():
    if request.method == 'GET':
        return redirect(url_for('landing'))
    if request.method == 'POST':

        if not global_config.config["SHEET_DEBUGGING"]:
            desc = request.form.get('characterPrompt')
            print("desc: ", desc)
            print(desc.strip() == "")
            
            character_json = brain.create_character_from_description(desc)
        else:
            character_json = character.test_character_json
        
    #character = character.Character(json=character_json)

    return render_template('character_sheet/character_sheet.html', character=character_json)

@bp.route('/upload', methods=['POST'])
def upload():
    if g.user is None:
        print("no user logged in")
        return jsonify({"error": "Authentication required"}), 401
    
    character = request.form.get('characterJSON')
    if not character:
        return jsonify({"error": "No character JSON uploaded"}), 400
    
    character = json.loads(character)  # Convert string back to object
    file = request.files.get('image')

    image_string = None
    
    if file:
        file_size = request.content_length
    
        if file_size > 5 * 1024 * 1024:
            return jsonify({"error": "IMG file too big!"}), 400

        img = Image.open(file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70, optimize=True)

        image_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
    else:
        print("no avatar provided")
    print(character)

    character['creator_id'] = g.user['_id']  # Link to User
    character['avatar_base64'] = image_string

    try:
        # 4. Insert into Characters Collection
        char_col = current_app.db['Characters']
        result = char_col.insert_one(character)
        char_id = result.inserted_id

        # 5. Update the User's character list
        users_col = current_app.db['Users']
        users_col.update_one(
            {"_id": g.user['_id']},
            {"$push": {"Characters": char_id}}
        )
        return jsonify({"success": True, "character_id": str(char_id)}), 201
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    
        
    # data = file.read()
    # mimetype = file.mimetype
    #     # compress image ?
    

    # doc = db.images.insert_one({"data": Binary(file.read()), "mimetype": file.mimetype})
    

