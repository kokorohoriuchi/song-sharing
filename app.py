from flask import Flask
from flask import session
import config

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/page1")
def page1():
    session["test"] = "aybabtu"
    return "Istunto asetettu"

@app.route("/page2")
def page2():
    return "Tieto istunnosta: " + session["test"]
