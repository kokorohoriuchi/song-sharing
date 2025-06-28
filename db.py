import sqlite3
import os
from flask import g, current_app

def init_db(app):
    """Initialize database connection handling"""
    app.teardown_appcontext(close_connection)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

def get_connection():
    """Get or create database connection"""
    if 'db' not in g:
        db_path = current_app.config["DATABASE"]
        g.db = sqlite3.connect(db_path)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_connection(exception=None):
    """Close database connection"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def execute(sql, params=[]):
    """Execute SQL command"""
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid
    return result

def query(sql, params=(), as_dict=False):
    """Execute SQL query and return results"""
    con = get_connection()
    cur = con.execute(sql, params)
    
    if as_dict:
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    return cur.fetchall()

def last_insert_id():
    """Get the last inserted row ID"""
    return g.get("last_insert_id", None)

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    return query("""
        SELECT 
            COUNT(songs.id) as song_count,
            COUNT(DISTINCT songs.artist) as unique_artists,
            COUNT(DISTINCT song_classifications.genre_id) as unique_genres
        FROM songs
        LEFT JOIN song_classifications ON songs.id = song_classifications.song_id
        WHERE songs.user_id = ?
    """, (user_id,), as_dict=True)[0]

def get_user_songs(user_id, limit=5):
    """Get recent songs added by user"""
    return query("""
        SELECT songs.*, 
               GROUP_CONCAT(DISTINCT genres.name) as genres,
               GROUP_CONCAT(DISTINCT styles.name) as styles
        FROM songs
        LEFT JOIN song_classifications ON songs.id = song_classifications.song_id
        LEFT JOIN genres ON song_classifications.genre_id = genres.id
        LEFT JOIN styles ON song_classifications.style_id = styles.id
        WHERE songs.user_id = ?
        GROUP BY songs.id
        ORDER BY songs.id DESC
        LIMIT ?
    """, (user_id, limit), as_dict=True)
