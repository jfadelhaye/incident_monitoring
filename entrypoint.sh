#!/bin/sh
set -e

# Ensure data directory exists and is writable
DATA_DIR=${DATA_DIR:-/app/data}
mkdir -p "$DATA_DIR"
chmod 755 "$DATA_DIR"

# Ensure log file exists
mkdir -p /var/log
touch /var/log/collector.log

# Load crontab
crontab /app/crontab

# Start cron in background
cron

# Run one collection on startup so DB isn't empty
python /app/run_collector.py

# Run Flask app (foreground)
python /app/run.py

