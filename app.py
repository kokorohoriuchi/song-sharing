from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Welcome to the app!"

@app.route("/page1")
def page1():
    return "First page"

@app.route("/page2")
def page2():
    return "Second page"
