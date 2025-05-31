DROP INDEX IF EXISTS idx_thread_messages;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS threads;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    image BLOB
);

CREATE TABLE threads (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES users,
    thread_id INTEGER NOT NULL REFERENCES threads
);

CREATE INDEX idx_thread_messages ON messages (thread_id);
