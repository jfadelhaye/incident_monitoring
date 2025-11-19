import os

# Use absolute path that aligns with Docker volume mapping
DB_PATH = "/app/events.db" if os.path.exists("/app") else "events.db"

FEEDS =  [
    {
        "name": "GitHub",
        "url": "https://www.githubstatus.com/history.rss",
        "color": "#24292e",
    },
    {
        "name": "Docker",
        "url": "https://www.dockerstatus.com/pages/533c6539221ae15e3f000031/rss",
        "color": "#0db7ed",
    },
    {
        "name": "Cloudflare",
        "url": "https://www.cloudflarestatus.com/history.rss",
        "color": "#f38020",
    },
    {
        "name": "Linear",
        "url": "https://linearstatus.com/feed.rss",
        "color": "#717ce1",
    },
    {
        "name": "Notion",
        "url": "https://www.notion-status.com/history.rss",
        "color": "#6f6f6f",
    }
]

