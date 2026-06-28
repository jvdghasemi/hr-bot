import sqlite3

conn = sqlite3.connect("faq.db")
cursor = conn.cursor()

# نمایش جدول‌ها
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables:")
for table in tables:
    print(table[0])

print("\nColumns:")

for table in tables:
    print(f"\n--- {table[0]} ---")
    cursor.execute(f"PRAGMA table_info({table[0]});")
    for column in cursor.fetchall():
        print(column)

conn.close()

conn = sqlite3.connect("faq.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM faq")
print(cursor.fetchone())

conn.close()
