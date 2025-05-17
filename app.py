from flask import Flask
import db

app = Flask(__name__)

@app.route("/")
def index():
    db.execute("INSERT INTO visits (visited_at) VALUES (datetime('now'))")
    result = db.query("SELECT COUNT(*) FROM visits")
    count = result[0][0]
    return "Sivua on ladattu " + str(count) + " kertaa"
