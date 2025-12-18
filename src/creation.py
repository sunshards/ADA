from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from . import global_config
from . import brain
from . import character
import json

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
    character = request.form.get('characterJSON')
    if character:
        character = json.loads(character)  # Convert string back to object
    file = request.files.get('image')
    if not json:
        return jsonify({"error": "No character JSON uploaded"}), 400
    if file:
        data = file.read()
        mimetype = file.mimetype
        # compress image ?
    else:
        print("no avatar provided")
    print(character)

    # doc = db.images.insert_one({"data": Binary(file.read()), "mimetype": file.mimetype})
    return jsonify({"success": True}), 200 #"id": str(doc.inserted_id)})

