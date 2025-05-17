from flask import Flask
from flask import redirect, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    db = sqlite3.connect("database.db")
    messages = db.execute("SELECT content FROM messages").fetchall()
    db.close()
    count = len(messages)
    return render_template("index.html", count=count, messages=messages)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO messages (content) VALUES (?)", [content])
    db.commit()
    db.close()
    return redirect("/")
