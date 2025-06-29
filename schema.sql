CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    image BLOB
);

CREATE TABLE threads (
    id INTEGER PRIMARY KEY,
    title TEXT,
    user_id INTEGER REFERENCES users
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    content TEXT,
    sent_at TEXT,
    user_id INTEGER REFERENCES users,
    thread_id INTEGER REFERENCES threads
);

CREATE INDEX idx_thread_messages ON messages (thread_id);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS styles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS song_classifications (
    song_id INTEGER NOT NULL,
    genre_id INTEGER,
    style_id INTEGER,
    FOREIGN KEY (song_id) REFERENCES songs(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id),
    FOREIGN KEY (style_id) REFERENCES styles(id),
    PRIMARY KEY (song_id, genre_id, style_id)
);

INSERT OR IGNORE INTO genres (name) VALUES 
("pop"), ("hiphop"), ("rap"), ("electronic"), ("indie"), 
("country"), ("jazz"), ("R&B"), ("rock");

INSERT OR IGNORE INTO styles (name) VALUES 
("industrial"), ("blues"), ("alternative"), ("underground"), 
("lo-fi"), ("instrumental");
