from flask import Flask
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    db.commit()
    result = db.execute("SELECT COUNT(*) FROM visits").fetchone()
    count = result[0]
    db.close()
    return "Sivua on ladattu " + str(count) + " kertaa"
