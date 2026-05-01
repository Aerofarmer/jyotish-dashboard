from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "kundli-vedic-secret-2024")
    CORS(app)

    from .routes import main
    app.register_blueprint(main)

    return app
