import sqlite3
import os
from schema import schema

def init_db():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect('instance/site.db')
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
