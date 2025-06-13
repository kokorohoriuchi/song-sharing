from flask import g, current_app
import sqlite3
import os

def init_db(app):
    """Initialize database connection handling"""
    app.teardown_appcontext(close_connection)
    
    # Ensure instance folder exists
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

def get_connection():
    """Get or create database connection"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_connection(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def execute(sql, params=[]):
    """Execute SQL command"""
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid

def query(sql, params=[]):
    """Execute SQL query"""
    con = get_connection()
    return con.execute(sql, params).fetchall()
