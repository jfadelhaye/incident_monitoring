from flask import Flask
import sqlite3
import os
from app.config import DB_PATH, DATA_DIR
from app.services.collector import init_db

def create_app():
    app = Flask(__name__)
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Ensure database exists at startup
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app