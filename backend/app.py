import logging
import secrets
from pathlib import Path
from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from backend.config import Config
from backend.extensions import cors, db, limiter
from backend.routes.api import api
from backend.routes.pages import pages
from backend.services.storage import create_storage


def create_app(test_config=None):
    app = Flask(__name__, static_folder=str(Path(__file__).resolve().parent.parent / "frontend"), static_url_path="")
    app.config.from_object(Config)
    app.config["FRONTEND_DIR"] = Path(__file__).resolve().parent.parent / "frontend"
    if test_config: app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_urlsafe(64)
        app.logger.warning("SECRET_KEY is not configured; using an ephemeral key for this process.")
    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_FILE_SIZE_MB"] * 1024 * 1024 * app.config["MAX_FILES_PER_SHARE"] + 1024 * 1024
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    limiter.init_app(app)
    cors_origins = app.config.get("CORS_ORIGINS", ["https://quickdropfiles.vercel.app"])
    if isinstance(cors_origins, str):
        cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/api/*": {"origins": cors_origins}})
    app.extensions["storage"] = create_storage(app.config)
    app.register_blueprint(api)
    app.register_blueprint(pages)
    app.logger.setLevel(logging.INFO)
    with app.app_context(): db.create_all()

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_): return jsonify(error="Request is too large."), 413

    @app.errorhandler(429)
    def rate_limited(_): return jsonify(error="Too many requests. Please try again later."), 429

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")
        return response
    return app


app = create_app()
