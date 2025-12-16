from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
import pymongo

bp = Blueprint('landing', __name__,)

@bp.route('/')
def landing():
    users = current_app.db.users.find()
    return render_template('landing/landing.html')