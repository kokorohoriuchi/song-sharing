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

def close_connection():
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
    
