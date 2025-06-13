from db import execute, query, last_insert_id
from flask import current_app

def add_song(title, artist, user_id):
    """Add a new song"""
    execute(
        "INSERT INTO songs (title, artist, user_id) VALUES (?, ?, ?)",
        [title, artist, user_id]
    )
    return last_insert_id()

def get_all_songs():
    """Get all songs with their classifications and owner username"""
    songs = query("""
        SELECT s.id, s.title, s.artist, s.user_id, u.username
        FROM songs s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.title
    """)
    
    for song in songs:
        song["genres"] = query("""
            SELECT g.id, g.name 
            FROM genres g
            JOIN song_classifications sc ON g.id = sc.genre_id
            WHERE sc.song_id = ?
        """, [song["id"]])
        
        song["styles"] = query("""
            SELECT s.id, s.name 
            FROM styles s
            JOIN song_classifications sc ON s.id = sc.style_id
            WHERE sc.song_id = ?
        """, [song["id"]])
    
    return songs

def get_song(song_id):
    """Get a single song by ID"""
    result = query("""
        SELECT s.id, s.title, s.artist, s.user_id, u.username
        FROM songs s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = ?
    """, [song_id])
    return result[0] if result else None

def update_song(song_id, title, artist):
    """Update song details"""
    execute(
        "UPDATE songs SET title = ?, artist = ? WHERE id = ?",
        [title, artist, song_id]
    )

def delete_song(song_id):
    """Delete a song"""
    execute("DELETE FROM songs WHERE id = ?", [song_id])
