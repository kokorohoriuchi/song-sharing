import math, secrets, sqlite3
import os
import click
from flask.cli import with_appcontext
from flask import Flask
from flask import abort, flash, make_response, redirect, render_template, request, session, url_for
from functools import wraps
import markupsafe
import config, forum, users
import classifications
import songs
from db import init_db, execute, query

app = Flask(__name__)
app.secret_key = config.secret_key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["DATABASE"] = os.path.join(basedir, "instance", "database.db")
init_db(app)

def require_login(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped_view

def verify_login():
    if 'user_id' not in session:
        abort(403)

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    stats = query("""
        SELECT 
            COUNT(songs.id) as song_count,
            COUNT(DISTINCT songs.artist) as unique_artists,
            COUNT(DISTINCT sc.genre_id) as unique_genres,
            COUNT(DISTINCT sc.style_id) as unique_styles
        FROM songs
        LEFT JOIN song_classifications sc ON songs.id = sc.song_id
        WHERE songs.user_id = ?
    """, (user_id,), as_dict=True)
    return stats[0] if stats else {
        "song_count": 0,
        "unique_artists": 0,
        "unique_genres": 0,
        "unique_styles": 0
    }

def get_user_songs(user_id, limit=5):
    """Get recent songs added by user"""
    return query("""
        SELECT songs.*, 
               GROUP_CONCAT(DISTINCT g.name) as genres,
               GROUP_CONCAT(DISTINCT s.name) as styles
        FROM songs
        LEFT JOIN song_classifications sc ON songs.id = sc.song_id
        LEFT JOIN genres g ON sc.genre_id = g.id
        LEFT JOIN styles s ON sc.style_id = s.id
        WHERE songs.user_id = ?
        GROUP BY songs.id
        ORDER BY songs.id DESC
        LIMIT ?
    """, (user_id, limit), as_dict=True)

@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database"""
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            image BLOB
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (thread_id) REFERENCES threads(id)
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    
    execute("""
        CREATE TABLE IF NOT EXISTS song_classifications (
            song_id INTEGER NOT NULL,
            genre_id INTEGER,
            style_id INTEGER,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
            FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE,
            PRIMARY KEY (song_id, genre_id, style_id)
        )
    """)
    
    default_genres = ["pop", "hiphop", "rap", "electronic", "indie", "country", "jazz", "R&B", "rock"]
    for genre in default_genres:
        execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", [genre])
    
    default_styles = ["industrial", "blues", "alternative", "underground", "lo-fi", "instrumental"]
    for style in default_styles:
        execute("INSERT OR IGNORE INTO styles (name) VALUES (?)", [style])
    
    click.echo("Initialized the database with all tables")

@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    try:
        thread_count = forum.thread_count()
        page_size = 10
        page_count = math.ceil(thread_count / page_size)
        page_count = max(page_count, 1)

        if page < 1:
            return redirect("/1")
        if page > page_count:
            return redirect("/" + str(page_count))

        threads = forum.get_threads(page, page_size)
        recent_songs = songs.get_recent_songs(limit=3)
        
        return render_template(
        "index.html",
        page=page,
        page_count=page_count,
        threads=threads,
        recent_songs=recent_songs
    )
        
    except sqlite3.OperationalError as e:
        flash("Database error. Please contact admin.")
        return render_template("error.html", error=str(e)), 500
        
@app.route("/search")
def search():
    query = request.args.get("query")
    results = forum.search(query) if query else []
    return render_template("search.html", query=query, results=results)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    try:
        user = query("""
            SELECT id, username, 
                   image IS NOT NULL as has_image
            FROM users 
            WHERE id = ?
        """, (user_id,), as_dict=True)
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")  
        user = query("""
            SELECT id, username, 
                   image IS NOT NULL as has_image
            FROM users 
            WHERE id = ?
        """, (user_id,), as_dict=True)
    
    if not user:
        abort(404)
    user = user[0]
    if 'created_at' not in user:
        user['created_at'] = None
    
    stats = get_user_stats(user_id)
    recent_songs = get_user_songs(user_id)
    messages = query("""
        SELECT m.id, m.content, m.sent_at, 
               t.id as thread_id, t.title as thread_title
        FROM messages m
        JOIN threads t ON m.thread_id = t.id
        WHERE m.user_id = ?
        ORDER BY m.sent_at DESC
    """, (user_id,), as_dict=True)
    
    return render_template(
        "user.html",
        user=user,
        stats=stats,
        recent_songs=recent_songs,
        messages=messages
    )
    
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
    verify_login()

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
    verify_login()

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
    verify_login()

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
    verify_login()

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
            flash("Registration successful! Please log in.")
            return redirect(url_for('login')) 
        except sqlite3.IntegrityError:
            flash("ERROR: The username you selected is already taken.")
            return render_template("register.html", filled={"username": username})

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
    verify_login()

    del session["user_id"]
    return redirect("/")

@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    verify_login()

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
    all_songs = songs.get_all_songs()  
    return render_template("songs/list.html", songs=all_songs)

@app.route("/songs/add", methods=["GET", "POST"])
@require_login
def add_song():
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
@require_login
def edit_song(song_id):
    song = songs.get_song(song_id)
    if not song or song['user_id'] != session['user_id']:
        abort(403)
        
    if request.method == "GET":
        song = songs.get_song(song_id)
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
    verify_login()
    check_csrf()
    
    song = songs.get_song(song_id)
    if not song or song["user_id"] != session["user_id"]:
        abort(403)
    
    songs.delete_song(song_id)
    flash("Song deleted successfully")
    return redirect("/songs")

@app.route("/songs/search")
def search_songs():
    try:
        search_term = request.args.get("q", "").strip()
        if not search_term:
            return redirect(url_for("list_songs"))
            
        results = songs.search_songs(search_term)
        return render_template("songs/list.html", 
                            songs=results, 
                            search_query=search_term)
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        flash("An error occurred during search")
        return redirect(url_for("list_songs"))
        
