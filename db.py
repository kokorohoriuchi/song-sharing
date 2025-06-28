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
            SUM(songs.duration) as total_duration,
            COUNT(DISTINCT songs.genre) as unique_genres
        FROM songs
        WHERE songs.user_id = ?
    """, (user_id,), as_dict=True)[0]

def get_user_songs(user_id, limit=5):
    """Get recent songs added by user"""
    return query("""
        SELECT * FROM songs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit), as_dict=True)
    
