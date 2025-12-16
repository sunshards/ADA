from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import pymongo

bp = Blueprint('landing', __name__,)

@bp.route('/', methods=('GET', 'POST'))
def landing():
    if request.method == 'POST':
        desc = None
        desc = request.form.get('characterPrompt')
        
        if not desc:
            error = 'Description is required.'
        else:
            print(desc)

    return render_template('landing/landing.html')