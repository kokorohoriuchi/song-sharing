from flask import Flask
from flask import redirect, render_template, request
import db

app = Flask(__name__)

@app.route("/")
def index():
    messages = db.query("SELECT content FROM messages")
    count = len(messages)
    return render_template("index.html", count=count, messages=messages)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]    
    db.execute("INSERT INTO messages (content) VALUES (?)", [content])
    return redirect("/")
