from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app, request, session
)
from bson.objectid import ObjectId

bp = Blueprint('selection', __name__, url_prefix='/selection')

@bp.route('/', methods=('GET', 'POST'))
def selection():
    characters_id = g.user["Characters"]

    player_characters = []
    for char_id in characters_id:
        char_query = current_app.db['Characters'].find_one({"_id": char_id})
        if char_query:
            player_characters.append({
                "id" : char_id,
                "name": char_query["name"],
                "_id": str(char_query["_id"]),
                "avatar_base64": char_query["avatar_base64"]
            })
    
    return render_template('character_selection/character_selection.html', characters=player_characters)

@bp.route('/set_character', methods=['POST'])
def set_character():
    if (request.method == 'POST'):
        character_id = request.get_json()['character_id']
        if not character_id:
            return jsonify({"error": "No character ID uploaded"}), 400
        session["character_id"] = character_id
        return jsonify({"success": True}), 200

@bp.route('/delete_character', methods=['POST'])
def delete_character():
    if g.user is None:
        return redirect(url_for('auth.login'))

    # Get ID from the hidden form field
    char_id_str = request.form.get('character_id')
    print(f"Character ID to delete: {char_id_str}")
    if char_id_str:
        char_id = ObjectId(char_id_str)

        # 1. Remove from Characters Collection
        current_app.db['Characters'].delete_one({
            "_id": char_id, 
            "creator_id": g.user["_id"]
        })

        # 2. Remove from User's List
        current_app.db['Users'].update_one(
            {"_id": g.user["_id"]},
            {"$pull": {"Characters": char_id}}
        )
        
        flash("Personaggio eliminato.", "info")

    # 3. Reload the page (Jinja will now render the updated list)
    return redirect(url_for('selection.selection'))
