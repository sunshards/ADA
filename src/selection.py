from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

bp = Blueprint('selection', __name__, url_prefix='/selection')

@bp.route('/', methods=('GET', 'POST'))
def creation():
    return render_template('character_sheet/character_sheet.html', characters=populated_character)

