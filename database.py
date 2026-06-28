import sqlite3

conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    chat_id INTEGER,
    name TEXT,
    username TEXT,
    text TEXT,
    voice_id TEXT,
    date TEXT,
    time TEXT
)
""")

cursor.execute("""

CREATE TABLE IF NOT EXISTS statistics(

    name TEXT PRIMARY KEY,

    count INTEGER DEFAULT 0

)

""")

conn.commit()


conn.commit()
