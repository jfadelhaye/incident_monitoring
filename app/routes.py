from flask import Blueprint, jsonify, render_template
from app.config import FEEDS
from app.models import get_events_from_db
from app.services.collector import update_feeds

main = Blueprint('main', __name__)

@main.route("/")
def index():
    return render_template("index.html", feeds=FEEDS)

@main.get("/api/events")
def api_events():
    events = get_events_from_db(hours=48)
    return jsonify(events)

@main.post("/refresh")
def refresh():
    update_feeds()
    return jsonify({"status": "ok"})