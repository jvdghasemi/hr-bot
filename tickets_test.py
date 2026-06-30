import os
import sqlite3

print("Current folder:", os.getcwd())
print("DB exists:", os.path.exists("tickets.db"))

conn = sqlite3.connect("tickets.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())

conn.close()
