from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from . import app
from . import character
import json

bp = Blueprint('creation', __name__, url_prefix='/creation')

@bp.route('/', methods=('GET', 'POST'))
def creation():
    if request.method == 'POST':
        desc = request.form.get('characterPrompt')
        character_json = app.create_character_from_description(desc)
        print(json.dumps(character_json, indent=2))

    return render_template('character_sheet/character_sheet.html', character=character.test_character)