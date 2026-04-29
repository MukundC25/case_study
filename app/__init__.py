from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    from app.routes.products import products_bp
    from app.routes.alerts import alerts_bp

    app.register_blueprint(products_bp)
    app.register_blueprint(alerts_bp)

    return app
