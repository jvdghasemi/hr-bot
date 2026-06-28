import os
import sqlite3
import pickle
import numpy as np
from ai.index import build_index
from ai.embedder import embed

DB_PATH = "faq.db"
DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT id, category, search_text, content
FROM faq
""")

rows = cursor.fetchall()

documents = []
embeddings = []

print(f"Found {len(rows)} FAQ items.")

for faq_id, category, search_text, content in rows:

    vector = embed(search_text)

    documents.append({
        "id": faq_id,
        "category": category,
        "search_text": search_text,
        "content": content
    })

    embeddings.append(vector)

conn.close()

embeddings = np.array(embeddings, dtype=np.float32)

with open("data/documents.pkl", "wb") as f:
    pickle.dump(documents, f)

np.save("data/embeddings.npy", embeddings)

build_index(embeddings)

print("Done!")
print(f"Documents: {len(documents)}")
print(f"Embeddings shape: {embeddings.shape}")
