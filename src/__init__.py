import os
from flask import Flask, render_template
from pymongo import MongoClient

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    # app.config.update(
    #     TESTING=True,
    #     EXPLAIN_TEMPLATE_LOADING=False
    # )

    CONNECTION_STRING = "mongodb+srv://ADAdmin:yR3BZdsB3gWXGgYo@clusterada.7tjhv8u.mongodb.net/?appName=ClusterADA"

    client = MongoClient(CONNECTION_STRING)
    app.mongo_client = client
    app.db = client["ADADatabase"]


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    stats = ["STR", "CON", "DEX", "INT", "WIS", "CHA"]
    combat_abilities = {
        "Sguardo Ammiccante": "Come azione bonus, il personaggio fissa un nemico entro 9 metri. Il bersaglio deve superare un tiro salvezza su Saggezza o avere svantaggio al prossimo attacco. Non funziona su costrutti, non morti o creature senza occhi.",
        "Conoscenza di Odori": "Il personaggio usa l’olfatto per individuare creature. Ottiene vantaggio alle prove per scoprire nemici nascosti entro 6 metri. Utile per evitare imboscate, non per infliggere danni.",
        "Contratto con l'ASL": "Una volta per combattimento, un nemico intelligente perde la reazione nel prossimo turno, distratto da norme di sicurezza e burocrazia evocata."
    }
    world_abilities = {
        "Palla di Fuego": "Crea una piccola sfera di fuoco innocua. Non infligge danni, ma può accendere oggetti, spaventare PNG o causare caos ambientale.",
        "Abilita Assurda": "Una volta al giorno, il personaggio dichiara una competenza improbabile. L’effetto è deciso dal master ed è sempre limitato e temporaneo.",
        "Colpo della Scimmia Furente": "Dimostrazione fisica esagerata che concede vantaggio alla prossima prova di Forza o Atletica, attirando però attenzioni indesiderate."
    }

    equip_items = {
        "Spada Fotonica": "Arma luminosa che ignora l’oscurità e illumina l’area circostante. Infligge danni normali, niente di più. L’effetto scenico è migliore della resa pratica.",
        "Coltello dei Fiori": "Piccola lama decorata. Utile per lavori di precisione o rituali strani. In combattimento è inferiore a qualsiasi arma seria.",
        "Pelle durissima": "Armatura naturale che aumenta leggermente la difesa. Non può essere rimossa e rende scomodi movimenti delicati. Protegge, ma limita.",
        "Scudo al contrario": "Scudo montato nel verso sbagliato. Fornisce una minima protezione frontale ma penalizza le prove di Destrezza. Idea pessima, ma qualcuno giura funzioni."
    }
    
    world_items =  {
        "Torcia Prismatica": "Torcia che emette luce multicolore. Non è più luminosa del normale, ma attira attenzione ovunque venga usata.",
        "Cubo Misterioso": "Cubo di origine sconosciuta. Non reagisce a nulla. Il master decide se serve a qualcosa o se è solo una perdita di tempo.",
        "Cubo Comune": "Un cubo assolutamente normale. Nessun effetto. È qui solo per confondere i giocatori.",
        "Carte del Divorzio": "Documenti legali incomprensibili. Possono causare disagio sociale o risolvere situazioni burocratiche molto specifiche."
    }

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

