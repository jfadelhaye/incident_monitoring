DB_PATH = "events.db"

FEEDS =  [
    {
        "name": "GitHub",
        "url": "https://www.githubstatus.com/history.rss",
    },
    {
        "name": "Docker",
        "url": "https://www.dockerstatus.com/pages/533c6539221ae15e3f000031/rss",
    },
    {
        "name": "Cloudflare",
        "url": "https://www.cloudflarestatus.com/history.rss",
    },
    {
        "name": "Linear",
        "url": "https://linearstatus.com/feed.rss",
    },
    {
        "name": "Notion",
        "url": "https://www.notion-status.com/history.rss",
    }
]

SOURCE_COLORS = {
    "GitHub": "#24292e",
    "Docker": "#0db7ed",
    "Cloudflare": "#f38020",
    "Linear": "#717ce1",
    "Notion": "#6f6f6f",
}

