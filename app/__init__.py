from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "kundli-vedic-secret-2024")
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    CORS(app)

    # Expose LLM config to templates via config.get(...)
    app.config["LLM_BASE_URL"] = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    app.config["LLM_MODEL"]    = os.getenv("LLM_MODEL", "")  # empty = AI notes off by default

    from .routes import main
    app.register_blueprint(main)

    return app
