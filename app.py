import math, secrets, sqlite3
from flask import Flask
from flask import abort, flash, make_response, redirect, render_template, request, session
import markupsafe
import config, forum, users
import classifications
import songs
from db import init_app

app = Flask(__name__)
app.secret_key = config.secret_key
classifications.initialize_classification_tables()
init_app(app)

@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

def require_login():
    if "user_id" not in session:
        abort(403)

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    thread_count = forum.thread_count()
    page_size = 10
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect("/" + str(page_count))

    threads = forum.get_threads(page, page_size)
    return render_template("index.html", page=page, page_count=page_count, threads=threads)

@app.route("/search")
def search():
    query = request.args.get("query")
    results = forum.search(query) if query else []
    return render_template("search.html", query=query, results=results)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    messages = users.get_messages(user_id)
    return render_template("user.html", user=user, messages=messages)

@app.route("/thread/<int:thread_id>")
def show_thread(thread_id):
    thread = forum.get_thread(thread_id)
    if not thread:
        abort(404)
    messages = forum.get_messages(thread_id)
    return render_template("thread.html", thread=thread, messages=messages)

@app.route("/new_thread", methods=["POST"])
def new_thread():
    check_csrf()
    require_login()

    title = request.form["title"]
    content = request.form["content"]
    if not title or len(title) > 100 or len(content) > 5000:
        abort(403)
    user_id = session["user_id"]

    thread_id = forum.add_thread(title, content, user_id)
    return redirect("/thread/" + str(thread_id))

@app.route("/new_message", methods=["POST"])
def new_message():
    check_csrf()
    require_login()

    content = request.form["content"]
    if len(content) > 5000:
        abort(403)
    user_id = session["user_id"]
    thread_id = request.form["thread_id"]

    try:
        forum.add_message(content, user_id, thread_id)
    except sqlite3.IntegrityError:
        abort(403)

    return redirect("/thread/" + str(thread_id))

@app.route("/edit/<int:message_id>", methods=["GET", "POST"])
def edit_message(message_id):
    require_login()

    message = forum.get_message(message_id)
    if not message or message["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("edit.html", message=message)

    if request.method == "POST":
        check_csrf()
        content = request.form["content"]
        if len(content) > 5000:
            abort(403)
        forum.update_message(message["id"], content)
        return redirect("/thread/" + str(message["thread_id"]))

@app.route("/remove/<int:message_id>", methods=["GET", "POST"])
def remove_message(message_id):
    require_login()

    message = forum.get_message(message_id)
    if not message or message["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("remove.html", message=message)

    if request.method == "POST":
        check_csrf()
        if "continue" in request.form:
            forum.remove_message(message["id"])
        return redirect("/thread/" + str(message["thread_id"]))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})

    if request.method == "POST":
        username = request.form["username"]
        if not username or len(username) > 16:
            abort(403)
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            flash("ERROR: The passwords you entered are not the same.")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

        try:
            users.create_user(username, password1)
            flash("Your account was created successfully, you can now log in.")
            return redirect("/")
        except sqlite3.IntegrityError:
            flash("ERROR: The ID you selected is already taken.")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next_page=request.referrer)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        next_page = request.form["next_page"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["csrf_token"] = secrets.token_hex(16)
            return redirect(next_page)
        else:
            flash("ERROR: Incorrect ID or password")
            return render_template("login.html", next_page=next_page)

@app.route("/logout")
def logout():
    require_login()

    del session["user_id"]
    return redirect("/")

@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    require_login()

    if request.method == "GET":
        return render_template("add_image.html")

    if request.method == "POST":
        check_csrf()

        file = request.files["image"]
        if not file.filename.endswith(".jpg"):
            flash("ERROR: The file you sent is not a jpg file")
            return redirect("/add_image")

        image = file.read()
        if len(image) > 100 * 1024:
            flash("ERROR: The file you sent is too large")
            return redirect("/add_image")

        user_id = session["user_id"]
        users.update_image(user_id, image)
        flash("Image added successfully")
        return redirect("/user/" + str(user_id))

@app.route("/image/<int:user_id>")
def show_image(user_id):
    image = users.get_image(user_id)
    if not image:
        abort(404)

    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response

@app.route("/songs")
def list_songs():
    """List all songs with their classifications"""
    all_songs = songs.get_all_songs()
    return render_template("songs/list.html", songs=all_songs)

@app.route("/songs/add", methods=["GET", "POST"])
def add_song():
    require_login()
    
    if request.method == "GET":
        genres = classifications.get_all_genres()
        styles = classifications.get_all_styles()
        return render_template("songs/add.html", genres=genres, styles=styles)
    
    if request.method == "POST":
        check_csrf()
        
        title = request.form["title"]
        artist = request.form["artist"]
        genre_ids = request.form.getlist("genres")
        style_ids = request.form.getlist("styles")
        
        if not title or not artist:
            flash("Title and artist are required")
            return redirect("/songs/add")
        
        try:
            song_id = songs.add_song(
                title=title,
                artist=artist,
                user_id=session["user_id"]
            )
            
            classifications.update_song_classifications(song_id, genre_ids, style_ids)
            
            flash("Song added successfully")
            return redirect("/songs")
        except Exception as e:
            flash(f"Error adding song: {str(e)}")
            return redirect("/songs/add")

@app.route("/songs/<int:song_id>/edit", methods=["GET", "POST"])
def edit_song(song_id):
    require_login()
    
    song = songs.get_song(song_id)
    if not song or song["user_id"] != session["user_id"]:
        abort(403)
    
    if request.method == "GET":
        genres = classifications.get_all_genres()
        styles = classifications.get_all_styles()
        current_genres = [g["id"] for g in classifications.get_song_genres(song_id)]
        current_styles = [s["id"] for s in classifications.get_song_styles(song_id)]
        
        return render_template(
            "songs/edit.html",
            song=song,
            genres=genres,
            styles=styles,
            current_genres=current_genres,
            current_styles=current_styles
        )
    
    if request.method == "POST":
        check_csrf()
        
        title = request.form["title"]
        artist = request.form["artist"]
        genre_ids = request.form.getlist("genres")
        style_ids = request.form.getlist("styles")
        
        if not title or not artist:
            flash("Title and artist are required")
            return redirect(f"/songs/{song_id}/edit")
        
        try:
            songs.update_song(
                song_id=song_id,
                title=title,
                artist=artist
            )
            
            classifications.update_song_classifications(song_id, genre_ids, style_ids)
            
            flash("Song updated successfully")
            return redirect("/songs")
        except Exception as e:
            flash(f"Error updating song: {str(e)}")
            return redirect(f"/songs/{song_id}/edit")

@app.route("/songs/<int:song_id>/delete", methods=["POST"])
def delete_song(song_id):
    require_login()
    check_csrf()
    
    song = songs.get_song(song_id)
    if not song or song["user_id"] != session["user_id"]:
        abort(403)
    
    songs.delete_song(song_id)
    flash("Song deleted successfully")
    return redirect("/songs")
