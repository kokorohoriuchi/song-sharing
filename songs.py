from db import execute, query, last_insert_id

def add_song(title, artist, user_id):
    """Add a new song"""
    execute(
        "INSERT INTO songs (title, artist, user_id) VALUES (?, ?, ?)",
        [title, artist, user_id]
    )
    return last_insert_id()

def get_song(song_id):
    """Get a song by ID"""
    result = query(
        "SELECT s.id, s.title, s.artist, s.user_id, u.username "
        "FROM songs s JOIN users u ON s.user_id = u.id "
        "WHERE s.id = ?",
        [song_id]
    )
    return result[0] if result else None

def get_all_songs():
    """Get all songs with the classifications"""
    songs = query(
        "SELECT s.id, s.title, s.artist, s.user_id, u.username "
        "FROM songs s JOIN users u ON s.user_id = u.id "
        "ORDER BY s.title"
    )
    
    for song in songs:
        song["genres"] = classification.get_song_genres(song["id"])
        song["styles"] = classification.get_song_styles(song["id"])
    
    return songs

def update_song(song_id, title, artist):
    """Update song details"""
    execute(
        "UPDATE songs SET title = ?, artist = ? WHERE id = ?",
        [title, artist, song_id]
    )

def delete_song(song_id):
    """Delete a song"""
    execute("DELETE FROM songs WHERE id = ?", [song_id])
