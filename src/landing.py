from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import pymongo

bp = Blueprint('landing', __name__,)

@bp.route('/')
def landing():
    return render_template('landing/landing.html')