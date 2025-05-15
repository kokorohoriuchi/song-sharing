from flask import Flask
from flask import render_template, request

app = Flask(__name__)

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/result", methods=["GET"])
def result():
    message = request.form["message"]
    return render_template("result.html", message=message) 
