from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app
)

bp = Blueprint('selection', __name__, url_prefix='/selection')

@bp.route('/', methods=('GET', 'POST'))
def selection():
    characters_id = g.user["Characters"]

    player_characters = []
    for char_id in characters_id:
        char_query = current_app.db['Characters'].find_one({"_id": char_id})
        if char_query:
            player_characters.append({
                "name": char_query["name"],
                "avatar_base64": char_query["avatar_base64"]
            })
    
    return render_template('character_selection/character_selection.html', characters=player_characters)

