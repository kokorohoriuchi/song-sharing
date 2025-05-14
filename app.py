from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/page1")
def page1():
    return "First page"

@app.route("/page2")
def page2():
    return "Second page"
