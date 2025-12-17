from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from . import app
from . import character
import json

bp = Blueprint('creation', __name__, url_prefix='/creation')

@bp.route('/', methods=('GET', 'POST'))
def creation():
    if request.method == 'GET':
        return redirect(url_for('landing'))
    if request.method == 'POST':
        desc = request.form.get('characterPrompt')
        print("desc: ", desc)
        print(desc.strip() == "")
        
        character_json = app.create_character_from_description(desc)
        print(json.dumps(character_json, indent=2))
        
    test_character = character.Character(json=character_json)

    return render_template('character_sheet/character_sheet.html', character=test_character)