import sqlite3
import os

def get_data_dir():
    # Respect XDG_DATA_HOME, fallback to ~/.local/share
    base_dir = os.environ.get('XDG_DATA_HOME')
    if not base_dir:
        base_dir = os.path.expanduser("~/.local/share")
    
    data_dir = os.path.join(base_dir, "misfitslauncher")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

DB_PATH = os.path.join(get_data_dir(), "games.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            app_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            store_source TEXT NOT NULL,
            is_installed INTEGER DEFAULT 0,
            last_played_timestamp INTEGER DEFAULT 0,
            install_timestamp INTEGER DEFAULT 0,
            umu_prefix_path TEXT,
            artwork_path TEXT,
            hero_path TEXT,
            logo_path TEXT,
            description TEXT,
            protondb_tier TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)
