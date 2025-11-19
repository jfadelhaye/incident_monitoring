from flask import Flask
import sqlite3
from app.config import DB_PATH
from app.services.collector import init_db

def create_app():
    app = Flask(__name__)
    
    # Ensure database exists at startup
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app