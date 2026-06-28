import sqlite3

conn = sqlite3.connect("faq.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM faq")
print(cursor.fetchone())

conn.close()
