from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError

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

        try:
            users_col = current_app.db['Users']
            user = users_col.find_one({"Email": email})
            
            if user is None:
                error = 'Incorrect email.'
            elif not check_password_hash(user["Password"], password):
                error = 'Incorrect password.'
                
        except Exception as e:
            error = f"An error occurred: {str(e)}"


        # flash(error)
        print(error)
        print(email, password)
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
        
        if error is None:
            # Hash the password
            hashed_password = generate_password_hash(password)
            
            # Prepare the user document
            user_doc = {
                "Username": username,
                "Email": email,
                "Password": hashed_password,
                "Characters": [],         # empty list for now
                "accountStatus": "active" # active after registration
            }

            try:
                users_col = current_app.db['Users']
                users_col.insert_one(user_doc)
                print(f"User {username} registered successfully!")
                return redirect(url_for('auth.login'))

            except DuplicateKeyError:
                print("A user with that username or email already exists.")
            except Exception as e:
                print(f"Registration failed: {str(e)}")


        print(username, email, password)
    return render_template('auth/register.html')