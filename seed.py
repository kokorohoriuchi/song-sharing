import random
import sqlite3

db = sqlite3.connect("database.db")

db.execute("DELETE FROM users")
db.execute("DELETE FROM threads")
db.execute("DELETE FROM messages")

user_count = 1000
thread_count = 10**6
message_count = 10**7

for i in range(1, user_count + 1):
    db.execute("INSERT INTO users (username) VALUES (?)",
               ["user" + str(i)])

for i in range(1, thread_count + 1):
    db.execute("INSERT INTO threads (title) VALUES (?)",
               ["thread" + str(i)])

for i in range(1, message_count + 1):
    user_id = random.randint(1, user_count)
    thread_id = random.randint(1, thread_count)
    db.execute("""INSERT INTO messages (content, sent_at, user_id, thread_id)
                  VALUES (?, datetime('now'), ?, ?)""",
               ["message" + str(i), user_id, thread_id])

db.commit()
db.close()
