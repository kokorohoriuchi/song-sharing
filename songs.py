from db import execute, query, last_insert_id

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
    """, as_dict=True)
    
    for song in songs:
        song["genres"] = query("""
            SELECT g.id, g.name 
            FROM genres g
            JOIN song_classifications sc ON g.id = sc.genre_id
            WHERE sc.song_id = ?
        """, [song["id"]], as_dict=True)
        
        song["styles"] = query("""
            SELECT s.id, s.name 
            FROM styles s
            JOIN song_classifications sc ON s.id = sc.style_id
            WHERE sc.song_id = ?
        """, [song["id"]], as_dict=True)
    
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

def get_recent_songs(limit=5):
    """Get recent songs with their classifications"""
    songs = query("""
        SELECT s.id, s.title, s.artist, s.user_id, u.username
        FROM songs s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.id DESC
        LIMIT ?
    """, [limit])
    
    songs_list = []
    for song in songs:
        song_dict = dict(song)
        song_dict["genres"] = query("""
            SELECT g.id, g.name 
            FROM genres g
            JOIN song_classifications sc ON g.id = sc.genre_id
            WHERE sc.song_id = ?
        """, [song_dict["id"]])
        
        song_dict["styles"] = query("""
            SELECT s.id, s.name 
            FROM styles s
            JOIN song_classifications sc ON s.id = sc.style_id
            WHERE sc.song_id = ?
        """, [song_dict["id"]])
        
        songs_list.append(song_dict)
    
    return songs_list

def search_songs(query_term):
    """Search songs by title or artist"""
    if not query_term:
        return []
    
    search_pattern = f"%{query_term}%"
    return query("""
        SELECT s.id, s.title, s.artist, s.user_id, u.username
        FROM songs s
        JOIN users u ON s.user_id = u.id
        WHERE s.title LIKE ? OR s.artist LIKE ?
        ORDER BY s.title
    """, [search_pattern, search_pattern], as_dict=True)
    
