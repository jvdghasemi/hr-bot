import sqlite3

conn = sqlite3.connect("faq.db")

c = conn.cursor()

c.execute("""

CREATE TABLE IF NOT EXISTS faq(

id INTEGER PRIMARY KEY,

question TEXT,

answer TEXT

)

""")


conn.commit()

conn.close()
