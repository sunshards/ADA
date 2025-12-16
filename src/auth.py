from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        flash(error)
    return render_template('auth/login.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'

        flash(error)
    return render_template('auth/register.html')