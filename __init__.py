from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_profiler

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://rikotenjikkenkou:p2a2smsywsoqrld@rikotenjikkenkou.mysql.pythonanywhere-services.com/rikotenjikkenkou$ticketdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True
    }
    db.init_app(app)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .handler import Handler
    handler = Handler()
    app.config['handler'] = handler

    # Flask-Profilerを有効化
    app.config["flask_profiler"] = {
        "enabled": True,
        "storage": {"engine": "sqlite"},
        "basicAuth": {"enabled": False},
        "ignore": ["^/static/.*"]
    }
    flask_profiler.init_app(app)

    with app.app_context():
        db.create_all()

    return app