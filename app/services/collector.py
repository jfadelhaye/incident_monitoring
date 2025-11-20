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

    # Check if this is an RSS feed or Atom feed
    is_atom = root.tag.endswith('}feed') or root.tag == 'feed'
    
    if is_atom:
        # Atom feeds use <entry> elements
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not items:
            items = root.findall(".//entry")  # fallback for feeds without namespace
    else:
        # RSS feeds use <item> elements
        items = root.findall(".//item")

    events: list[dict] = []

    for item in items:
        # Handle titles differently for RSS vs Atom
        if is_atom:
            title = (
                item.findtext("{http://www.w3.org/2005/Atom}title")
                or item.findtext("title")
                or ""
            ).strip()
        else:
            title = (item.findtext("title") or "").strip()
        
        if not title:
            title = "(no title)"
        
        # Handle links differently for RSS vs Atom
        link = ""
        if is_atom:
            # Atom feeds store links in <link href="..."/> attributes
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is None:
                link_el = item.find("link")
            if link_el is not None:
                link = (link_el.get("href") or "").strip()
        else:
            # RSS feeds store links in text content of <link> element
            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.text or "").strip()
        
        # Handle content/description differently for RSS vs Atom
        if is_atom:
            # Atom feeds use <content> and sometimes have XHTML content
            content_el = item.find("{http://www.w3.org/2005/Atom}content")
            summary_el = item.find("{http://www.w3.org/2005/Atom}summary")
            if content_el is None:
                content_el = item.find("content")
            if summary_el is None:
                summary_el = item.find("summary")
                
            if content_el is not None:
                # Handle XHTML content by extracting text from nested elements
                if content_el.get("type") == "xhtml":
                    # Get all text content from XHTML div
                    description = "".join(content_el.itertext()).strip()
                else:
                    description = (content_el.text or "").strip()
            elif summary_el is not None:
                description = (summary_el.text or "").strip()
            else:
                description = ""
        else:
            # RSS feeds use <description>
            description = (item.findtext("description") or "").strip()
        
        # Handle GUID/ID differently for RSS vs Atom
        if is_atom:
            atom_id = (
                item.findtext("{http://www.w3.org/2005/Atom}id")
                or item.findtext("id")
                or ""
            ).strip()
            guid = atom_id or link or (title + "|no-guid")
        else:
            guid = (
                (item.findtext("guid") or "").strip()
                or link
                or (title + "|no-guid")
            )

        # Handle dates - both formats can use updated/published
        if is_atom:
            raw_date = (
                item.findtext("{http://www.w3.org/2005/Atom}updated")
                or item.findtext("{http://www.w3.org/2005/Atom}published")
                or item.findtext("updated")
                or item.findtext("published")
            )
        else:
            raw_date = (
                item.findtext("pubDate")
                or item.findtext("dc:date")
                or item.findtext("updated")
                or item.findtext("published")
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


def main():
    """Main entry point for running collector as a module."""
    update_feeds()

if __name__ == "__main__":
    main()
