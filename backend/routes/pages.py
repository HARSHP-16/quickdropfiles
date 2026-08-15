from flask import Blueprint, current_app, send_from_directory

pages = Blueprint("pages", __name__)


@pages.get("/")
def home(): return send_from_directory(current_app.config["FRONTEND_DIR"], "index.html")

@pages.get("/open")
def open_page(): return send_from_directory(current_app.config["FRONTEND_DIR"], "open.html")

@pages.get("/s/<token>")
def share_page(token): return send_from_directory(current_app.config["FRONTEND_DIR"], "share.html")

@pages.get("/expired")
def expired(): return send_from_directory(current_app.config["FRONTEND_DIR"], "expired.html")
