import sqlite3


def load_faq():
    conn = sqlite3.connect("faq.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, category, search_text, content FROM faq")
    rows = cursor.fetchall()

    conn.close()

    faq_data = []

    for r in rows:
        faq_data.append({
            "id": r[0],
            "category": r[1],
            "search_text": r[2],
            "content": r[3]
        })

    return faq_data


if __name__ == "__main__":
    data = load_faq()
    for d in data:
        print(d["category"])
