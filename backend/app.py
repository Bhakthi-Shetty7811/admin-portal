import os
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS

from models import db
from blueprints.auth import auth_bp
from blueprints.opportunities import opp_bp

# Load environment variables from .env before anything else
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    # ── Config ──────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"]           = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///sky.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)

    # CORS: allow the frontend (file:// or localhost) to call our API.
    # In production you'd restrict this to your real domain.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Blueprints ──────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(opp_bp)

    # ── Serve the frontend ───────────────────────────────────────────────────
    # This lets you open http://localhost:5000 and get admin.html directly,
    # without needing a separate web server for the static files.
    @app.route("/")
    def serve_index():
        return send_from_directory("../sky", "admin.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        return send_from_directory("../sky", filename)

    # ── Create tables ────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        print("[DB] Tables ready.")

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5000)