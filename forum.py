from db import query, execute

def thread_count():
    result = query("SELECT COUNT(*) FROM threads")
    return result[0][0] if result else 0

def get_threads(page, page_size):
    offset = (page - 1) * page_size
    return query("""
        SELECT t.id, t.title, t.created_at, u.username 
        FROM threads t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    """, [page_size, offset])

def get_thread(thread_id):
    sql = "SELECT id, title FROM threads WHERE id = ?"
    result = db.query(sql, [thread_id])
    return result[0] if result else None

def get_messages(thread_id):
    sql = """SELECT m.id, m.content, m.sent_at, m.user_id, u.username
             FROM messages m, users u
             WHERE m.user_id = u.id AND m.thread_id = ?
             ORDER BY m.id"""
    return db.query(sql, [thread_id])

def get_message(message_id):
    sql = "SELECT id, content, user_id, thread_id FROM messages WHERE id = ?"
    result = db.query(sql, [message_id])
    return result[0] if result else None

def add_thread(title, content, user_id):
    sql = "INSERT INTO threads (title, user_id) VALUES (?, ?)"
    db.execute(sql, [title, user_id])
    thread_id = db.last_insert_id()
    add_message(content, user_id, thread_id)
    return thread_id

def add_message(content, user_id, thread_id):
    sql = """INSERT INTO messages (content, sent_at, user_id, thread_id) VALUES
             (?, datetime('now'), ?, ?)"""
    db.execute(sql, [content, user_id, thread_id])

def update_message(message_id, content):
    sql = "UPDATE messages SET content = ? WHERE id = ?"
    db.execute(sql, [content, message_id])

def remove_message(message_id):
    sql = "DELETE FROM messages WHERE id = ?"
    db.execute(sql, [message_id])

def search(query):
    sql = """SELECT m.id message_id,
                    m.thread_id,
                    t.title thread_title,
                    m.sent_at,
                    u.username
             FROM threads t, messages m, users u
             WHERE t.id = m.thread_id AND
                   u.id = m.user_id AND
                   m.content LIKE ?
             ORDER BY m.sent_at DESC"""
    return db.query(sql, ["%" + query + "%"])
