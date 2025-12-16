import os
from flask import Flask, render_template
from enum import Enum
import random
from pymongo import MongoClient

class Statistic(Enum):
    STR = "STR"
    CON = "CON"
    DEX = "DEX"
    INT = "INT"
    WIS = "WIS"
    CHA = "CHA"

class AlignmentMorality(Enum):
    GOOD = "Good"
    NEUTRAL = "Neutral"
    EVIL = "Evil"

class AlignmentRighteousness(Enum):
    LAWFUL = "Lawful"
    NEUTRAL = "Neutral"
    CHAOTIC = "Chaotic"

class Character:
    # livello
    # hp massimi
    # milestones

    def __init__(self, 
                 name : str, 
                 stats : dict[Statistic, int], 
                 combat_abilities : dict[str, str],
                 world_abilities: dict[str, str], 
                 equip_items: dict[str, str], 
                 world_items: dict[str, str], 
                 dnd_race: str,
                 dnd_class: str,
                 alignment_righteousness : AlignmentRighteousness,
                 alignment_morality : AlignmentMorality,
                 birthplace : str = "",
                 description : str = ""):
        self.name = name
        self.description = description
        self.stats = stats
        self.combat_abilities = combat_abilities
        self.world_abilities = world_abilities
        self.equip_items = equip_items
        self.world_items = world_items
        self.dnd_race = dnd_race
        self.dnd_class = dnd_class
        self.birthplace = birthplace
        self.alignment_morality = alignment_morality
        self.alignment_righteousness = alignment_righteousness

    def get_sheet_terms(self):
        return {
            "Race" : self.dnd_race,
            "Class" : self.dnd_class,
            "Alignment" : self.alignment_righteousness.value + " " + self.alignment_morality.value,
            "Birthplace" : self.birthplace
        }

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

    stats = {stat : random.randint(0,12) for stat in list(Statistic)}

    name = "Pippo"

    desc = "Lorem ipsum dolor sit amet consectetur adipisicing elit. Aliquam, itaque voluptatum harum tempore consequuntur rerum, tempora suscipit aliquid, qui ad provident dolorum repudiandae quisquam doloremque cum? Placeat, hic optio! Sapiente exercitationem vero molestiae doloribus, fugiat autem ullam nesciunt cumque dolores itaque eum illum aperiam optio eveniet earum! Sequi placeat nesciunt numquam dolor neque nostrum voluptatibus. Adipisci velit itaque incidunt dolorum, aperiam excepturi natus amet accusantium dolorem saepe architecto sequi quis tempora. Animi ratione fugit officia sed quis? Officiis qui optio est eaque corrupti iste, iusto, accusamus reprehenderit velit vel tempora soluta dolore at doloremque ipsum ipsa vero animi unde quidem."
    
    test_character = Character(name, 
                               stats, 
                               combat_abilities=combat_abilities, 
                               world_abilities=world_abilities, 
                               equip_items=equip_items, 
                               world_items=world_items,
                               dnd_race = "Orc",
                               dnd_class = "Mage",
                               alignment_righteousness = AlignmentRighteousness.LAWFUL,
                               alignment_morality = AlignmentMorality.GOOD,
                               birthplace = "Mordor", 
                               description=desc)

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

    app.add_url_rule('/', endpoint='landing')

    @app.route('/test-db')
    def test_db():
    # Try to list collections
        try:
            collections = app.db.list_collection_names()
            return f"MongoDB works! Collections: {collections}"
        except Exception as e:
            return f"MongoDB connection failed: {str(e)}"
    
    @app.route('/debug')
    def debug():
         print(app.url_for(('auth.login')))
         return 'Hello world'
    
    return app

