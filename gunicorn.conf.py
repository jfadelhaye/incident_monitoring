# Gunicorn configuration file
bind = "0.0.0.0:5042"
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True