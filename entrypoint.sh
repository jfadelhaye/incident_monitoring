#!/bin/sh
set -e

# Ensure log file exists
mkdir -p /var/log
touch /var/log/collector.log

# Load crontab
crontab /app/crontab

# Start cron in background
cron

# Run one collection on startup so DB isn't empty
python /app/collector.py

# Run Flask app (foreground)
python /app/app.py

