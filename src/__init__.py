import os
from flask import Flask, render_template
from pymongo import MongoClient

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'
    # app.config.update(
    #     TESTING=True,
    #     EXPLAIN_TEMPLATE_LOADING=False
    # )

    CONNECTION_STRING = "mongodb+srv://ADAdmin:yR3BZdsB3gWXGgYo@clusterada.7tjhv8u.mongodb.net/?appName=ClusterADA"

    client = MongoClient(CONNECTION_STRING)
    app.mongo_client = client
    
    app.db = client["ADADatabase"]

    users_col = app.db['Users']
    users_col.create_index('Email', unique=True)
    users_col.create_index('Username', unique=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    messages = [
        {"type": "out", "value": "a"},
        {"type": "out", "value": "b"},
        {"type": "in",  "value": "c"},
        {"type": "out", "value": "d"},
        {"type": "in",  "value": "e"},
        {"type": "out", "value": "f"},
        {"type": "out", "value": "g"},
        {"type": "out", "value": "g"},
        {"type": "out", "value": "g"},
        {"type": "out", "value": "g"},
    ]

    players = [
        {"username" : "Pippo", "MAX_HP": 10, "HP": 10, "percentage": 100},
        {"username" : "Giacomo", "MAX_HP": 23, "HP": 15, "percentage": 65.2},
        {"username" : "Anacleto", "MAX_HP": 11, "HP": 8, "percentage": 72.7 },
        {"username" : "Bimbo", "MAX_HP": 0, "HP": 0, "percentage": 0 }
    ]
    
    from . import landing
    app.register_blueprint(landing.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import creation
    app.register_blueprint(creation.bp)

    app.add_url_rule('/', endpoint='landing')

    # @app.route('/test-db')
    # def test_db():
    # # Try to list collections
    #     try:
    #         collections = app.db.list_collection_names()
    #         return f"MongoDB works! Collections: {collections}"
    #     except Exception as e:
    #         return f"MongoDB connection failed: {str(e)}"
    
    @app.route('/debug')
    def debug():
         print(app.url_for(('auth.login')))
         return 'Hello world'
    
    return app

