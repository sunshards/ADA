import os
import sys
from flask import Flask, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient

socketio = SocketIO()

def create_app(test_config=None):
    # Adding src to sys.path: (the list of paths python looks at to import things):
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    # print(sys.path)
    # create and configure the app
    app = Flask(__name__)

    app.config.update(
        TESTING=True,
        EXPLAIN_TEMPLATE_LOADING=False,
        SECRET_KEY = 'dev'
    )

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
    
    socketio.init_app(app)

    with app.app_context():
        from .landing import bp as landing_bp
        app.register_blueprint(landing_bp)

        from .auth import bp as auth_bp 
        app.register_blueprint(auth_bp)

        from .creation import bp as creation_bp
        app.register_blueprint(creation_bp)

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
