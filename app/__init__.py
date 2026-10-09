from flask import Flask
from .storage import initialize_data

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "safelink-local-secret-key"

    initialize_data()

    from .routes import main
    app.register_blueprint(main)

    return app
