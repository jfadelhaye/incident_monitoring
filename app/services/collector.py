import sqlite3
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests

from app.config import FEEDS, DB_PATH

def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT,
            description TEXT,
            pub_date TEXT NOT NULL, -- ISO 8601 in UTC
            guid TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_events_source_guid
        ON events(source, guid)
        """
    )
    conn.commit()

def parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None

    dt = None
    try:
        dt = parsedate_to_datetime(raw)
    except Exception:
        pass

    if dt is None:
        try:
            dt = datetime.fromisoformat(raw)
        except Exception:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def text_or_none(element, tag_name: str) -> str | None:
    if element is None:
        return None
    child = element.find(tag_name) 
    if child is not None and child.text:
        return child.text.strip()
    return None

def fetch_feed(feed) -> list[dict]:
    resp = requests.get(feed["url"], timeout=10)
    resp.raise_for_status()

    xml = resp.content
    root = ET.fromstring(xml)

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{*}entry")

    events: list[dict] = []

    for item in items:
        title = (item.findtext("title") or "").strip()
        if not title:
            title = "(no title)"
        link = ""
        link_el = item.find("link")
        if link_el is not None:
            link = (link_el.get("href") or link_el.text or "").strip()
        description = (
            item.findtext("description")
            or item.findtext("summary")
            or item.findtext("content")
            or ""
        ).strip()
        guid = (
            (item.findtext("guid") or "").strip()
            or (item.findtext("id") or "").strip()
            or link
            or (title + "|no-guid")
        )

        raw_date = (
            item.findtext("pubDate")
            or item.findtext("updated")
            or item.findtext("published")
            or item.findtext("dc:date")
            or item.findtext("{*}updated")
            or item.findtext("{*}published")
        )

        dt = parse_date(raw_date) if raw_date else None
        if dt is None:
            # skip items with no valid date
            continue

        events.append(
            {
                "source": feed["name"],
                "title": title,
                "link": link,
                "description": description,
                "guid": guid,
                "pub_date": dt.isoformat(),
            }
        )

    return events


def cleanup_old_events(conn: sqlite3.Connection) -> None:
    """Remove events older than 7 days based on pub_date."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_iso = cutoff_date.isoformat()
    
    cursor = conn.execute(
        "DELETE FROM events WHERE pub_date < ?",
        (cutoff_iso,)
    )
    deleted_count = cursor.rowcount
    if deleted_count > 0:
        print(f"[collector] Cleaned up {deleted_count} events older than 7 days")


def update_feeds() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        now = datetime.now(timezone.utc).isoformat()

        for feed in FEEDS:
            try:
                events = fetch_feed(feed)
            except Exception as e:
                print(f"[collector] Error fetching {feed['name']}: {e}")
                continue

            for ev in events:
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO events
                        (source, title, link, description, pub_date, guid, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ev["source"],
                            ev["title"],
                            ev["link"],
                            ev["description"],
                            ev["pub_date"],
                            ev["guid"],
                            now,
                        ),
                    )
                except Exception as e:
                    # don't kill the whole run on a bad row
                    print(f"[collector] Insert error for {feed['name']}: {e}")

        conn.commit()
        
        # Clean up old events after successful feed update
        cleanup_old_events(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    update_feeds()
