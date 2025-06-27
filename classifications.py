from flask import current_app
from db import execute, query

def initialize_classification_tables():
    """Initialize the classification tables"""
    with current_app.app_context():
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
    
        default_genres = [
            "pop", "hiphop", "rap", "electronic", "indie",
            "country", "jazz", "R&B", "rock"
        ]
        for genre in default_genres:
            execute(
                "INSERT OR IGNORE INTO genres (name) VALUES (?)",
                [genre]
            )
    
        default_styles = [
            "industrial", "blues", "alternative", "underground",
            "lo-fi", "instrumental"
        ]
        for style in default_styles:
            execute(
                "INSERT OR IGNORE INTO styles (name) VALUES (?)",
                [style]
            )

def get_all_genres():
    """Return all genre options"""
    return query("SELECT id, name FROM genres ORDER BY name")

def get_all_styles():
    """Return all style options"""
    return query("SELECT id, name FROM styles ORDER BY name")

def get_song_genres(song_id):
    """Get genres assigned to a song"""
    return query("""
        SELECT g.id, g.name 
        FROM genres g
        JOIN song_classifications sc ON g.id = sc.genre_id
        WHERE sc.song_id = ?
    """, [song_id])

def get_song_styles(song_id):
    """Get styles assigned to a song"""
    return query("""
        SELECT s.id, s.name 
        FROM styles s
        JOIN song_classifications sc ON s.id = sc.style_id
        WHERE sc.song_id = ?
    """, [song_id])

def update_song_classifications(song_id, genre_ids, style_ids):
    """Update all classifications for a song"""
    execute(
        "DELETE FROM song_classifications WHERE song_id = ?",
        [song_id]
    )
    
    for genre_id in genre_ids:
        execute(
            "INSERT INTO song_classifications (song_id, genre_id) VALUES (?, ?)",
            [song_id, int(genre_id)]
        )
    
    for style_id in style_ids:
        execute(
            "INSERT INTO song_classifications (song_id, style_id) VALUES (?, ?)",
            [song_id, int(style_id)]
        )

def get_songs_by_genre(genre_id):
    """Get all songs with a specific genre"""
    return query("""
        SELECT s.id, s.title, s.artist 
        FROM songs s
        JOIN song_classifications sc ON s.id = sc.song_id
        WHERE sc.genre_id = ?
        ORDER BY s.title
    """, [genre_id])

def get_songs_by_style(style_id):
    """Get all songs with a specific style"""
    return query("""
        SELECT s.id, s.title, s.artist 
        FROM songs s
        JOIN song_classifications sc ON s.id = sc.song_id
        WHERE sc.style_id = ?
        ORDER BY s.title
    """, [style_id])
