# Incident Checker

![Timeline Screenshot](app/templates/dead_docker.png)

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
# With persistent database storage
docker run -p 5042:5042 -v incident_data:/app/events.db judelhaye/incident-checker:latest

# Or using a bind mount to current directory
docker run -p 5042:5042 -v $(pwd)/data:/app judelhaye/incident-checker:latest
```

### Using Docker Compose

```bash
git clone <repository-url>
cd incident_checker
docker-compose up
```

The application will be available at http://localhost:5042

Docker Compose automatically creates a named volume `incident_data` to persist the SQLite database across container recreations.

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run initial feed collection
python -m app.services.collector

# Start the Flask application
python run.py
```

Visit http://localhost:5042 to view the timeline.

## Architecture

- **Flask Web Server** (`run.py` + `app/`): Serves the timeline interface and provides API endpoints
- **Feed Collector** (`app/services/collector.py`): Fetches RSS feeds and stores incidents in SQLite
- **SQLite Database** (`events.db`): Stores incident data with deduplication
- **Responsive Frontend**: Single-page timeline with embedded JavaScript
- **Automated Collection**: Hourly cron job updates incident data

## Configuration

### Adding New Status Feeds

Edit `app/config.py` to add new RSS feeds:

```python
FEEDS = [
    {
        "name": "Service Name",
        "url": "https://status.example.com/history.rss",
        "color": "#ff5733",  # Custom color for timeline
    }
]
```

## API Endpoints

- `GET /`: Main timeline interface
- `GET /api/events`: JSON API returning incidents from last 48 hours
- `POST /refresh`: Manually trigger feed collection


## Development

### Project Structure

```
.
├── run.py                 # Application entry point
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # Service URLs and configuration
│   ├── models.py          # Database functions
│   ├── routes.py          # Route handlers (Blueprint-based)
│   ├── services/
│   │   └── collector.py   # RSS feed collector
│   ├── static/            # Static files
│   └── templates/
│       └── index.html     # Timeline interface
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

- **Styling**: Modify CSS in `app/templates/index.html`
- **Feed Sources**: Update `app/config.py` to add/remove status feeds
- **Collection Schedule**: Edit `crontab` to change collection frequency
- **Time Window**: Adjust the hours parameter in API endpoints

### Manual Feed Collection

```bash
# Run feed collection manually
python -m app.services.collector
```