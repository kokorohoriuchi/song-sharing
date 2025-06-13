from flask import g, current_app
import sqlite3
import os

def get_connection():
    if 'db' not in g:
        os.makedirs(os.path.dirname(current_app.config['DATABASE']), exist_ok=True)
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_connection(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_connection)

def execute(sql, params=[]):
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid

def query(sql, params=[]):
    con = get_connection()
    return con.execute(sql, params).fetchall()

def last_insert_id():
    return g.get('last_insert_id')
