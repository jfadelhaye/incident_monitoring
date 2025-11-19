import sqlite3
from datetime import datetime, timedelta, timezone
from app.config import DB_PATH, FEEDS

def get_events_from_db(hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_iso = cutoff.isoformat()
    cutafter_iso = datetime.now(timezone.utc).isoformat()

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