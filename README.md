# Incident Checker

![Timeline Screenshot](templates/dead_docker.png)

A Python Flask web application that aggregates and displays service status incidents from various tech companies' RSS feeds. Monitor incidents and maintenance windows from GitHub, Docker, Cloudflare, Linear, and Notion in a unified timeline interface.

## Features

- **Hourly Status Monitoring**: Automatically collects incident reports from major service providers every hours
- **Visual Timeline**: Clean, responsive interface showing incidents chronologically
- **Status Indication**: Green headers for resolved incidents, orange for ongoing/unresolved
- **Manual Refresh**: Force immediate feed collection via web interface
- **Docker Ready**: Containerized application with automated collection via cron
- **Responsive Design**: Works on desktop and mobile devices

## Monitored Services

- GitHub Status
- Docker Status  
- Cloudflare Status
- Linear Status
- Notion Status

## Quick Start

### Running from Docker Hub

```bash
docker run -p 5042:5042 judelhaye/incident-checker:latest
```

### Using Docker Compose

```bash
git clone <repository-url>
cd incident_checker
docker-compose up
```

The application will be available at http://localhost:5042

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run initial feed collection
python collector.py

# Start the Flask application
python app.py
```

Visit http://localhost:5042 to view the timeline.

## Architecture

- **Flask Web Server** (`app.py`): Serves the timeline interface and provides API endpoints
- **Feed Collector** (`collector.py`): Fetches RSS feeds and stores incidents in SQLite
- **SQLite Database** (`events.db`): Stores incident data with deduplication
- **Responsive Frontend**: Single-page timeline with embedded JavaScript
- **Automated Collection**: Hourly cron job updates incident data

## Configuration

### Adding New Status Feeds

Edit `config.py` to add new RSS feeds:

```python
FEEDS = [
    {
        "name": "Service Name",
        "url": "https://status.example.com/history.rss",
    }
]

SOURCE_COLORS = {
    "Service Name": "#ff5733",  # Custom color for timeline
}
```

## API Endpoints

- `GET /`: Main timeline interface
- `GET /api/events`: JSON API returning incidents from last 48 hours
- `POST /refresh`: Manually trigger feed collection


## Development

### Project Structure

```
.
├── app.py                 # Flask web application
├── collector.py           # RSS feed collector
├── config.py              # Service URLs and configuration
├── templates/
│   └── index.html         # Timeline interface
├── docker-compose.yml     # Deployment compose file
├── Dockerfile             # Container build configuration
├── requirements.txt       # Python dependencies
└── crontab                # Scheduled collection configuration
```

### Database Schema

The SQLite database contains an `events` table:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT,
    description TEXT,
    pub_date TEXT NOT NULL,  -- ISO 8601 in UTC
    guid TEXT,
    created_at TEXT NOT NULL
);
```

Events are automatically deduplicated using a unique index on `(source, guid)`.

### Customization

- **Styling**: Modify CSS in `templates/index.html`
- **Feed Sources**: Update `config.py` to add/remove status feeds
- **Collection Schedule**: Edit `crontab` to change collection frequency
- **Time Window**: Adjust the hours parameter in API endpoints