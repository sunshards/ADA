from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
import pymongo

bp = Blueprint('landing', __name__)

@bp.route('/')
def landing():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["mydatabase"]
    print(myclient.list_database_names())
    return render_template('landing.html')