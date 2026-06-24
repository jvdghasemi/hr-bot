import sqlite3

conn = sqlite3.connect("tickets.db")  # یا bot.db همون که استفاده می‌کنی
cursor = conn.cursor()

cursor.execute("SELECT * FROM tickets")
rows = cursor.fetchall()

print("ALL TICKETS:")
for r in rows:
    print(r)

conn.close()

for row in rows:
    print("FUUL ROW", row)
