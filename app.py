# app.py
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Flask, Response, jsonify, render_template

from config import DB_PATH, FEEDS
from collector import update_feeds

app = Flask(__name__)

def get_events_from_db(hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_iso = cutoff.isoformat()
    cutafter_iso = datetime.now(timezone.utc).isoformat()

    # Create color lookup from FEEDS
    feed_colors = {feed["name"]: feed["color"] for feed in FEEDS}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT source, title, link, description, pub_date
            FROM events
            WHERE pub_date >= ?
            AND pub_date < ?
            ORDER BY pub_date DESC
            """,
            (cutoff_iso,cutafter_iso),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    events: list[dict] = []
    for row in rows:
        source = row["source"]
        events.append(
            {
                "source": source,
                "title": row["title"],
                "link": row["link"],
                "description": row["description"],
                "pub_date": row["pub_date"],
                "color": feed_colors.get(source, "#555555"),
            }
        )
    return events

@app.route("/")
def index():
    return render_template("index.html", feeds=FEEDS)

@app.get("/api/events")
def api_events():
    events = get_events_from_db(hours=48)
    return jsonify(events)


@app.post("/refresh")
def refresh():
    # Trigger the collector manually
    update_feeds()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5042, debug=False)

