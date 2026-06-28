"""
Run this script once to build/rebuild the FAISS index from faq.db:
    python -m ai.build_index
"""
import os
import sqlite3
import pickle
import numpy as np
import faiss
from .model import model
from .settings import DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect("faq.db")
cursor = conn.cursor()
cursor.execute("SELECT id, category, search_text, content FROM faq")
rows = cursor.fetchall()
conn.close()

print(f"Building index from {len(rows)} FAQ items...")

documents = []
embeddings = []

for faq_id, category, search_text, content in rows:
    vector = model.encode(search_text, normalize_embeddings=True)
    documents.append({
        "id": faq_id,
        "category": category,
        "search_text": search_text,
        "content": content,
    })
    embeddings.append(vector)

embeddings_np = np.array(embeddings, dtype=np.float32)

# Save documents
with open(os.path.join(DATA_DIR, "documents.pkl"), "wb") as f:
    pickle.dump(documents, f)

# Save embeddings
np.save(os.path.join(DATA_DIR, "embeddings.npy"), embeddings_np)

# Build and save FAISS index
dimension = embeddings_np.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings_np)
faiss.write_index(index, os.path.join(DATA_DIR, "faiss.index"))

print(f"Done! {len(documents)} documents indexed.")
print(f"Embeddings shape: {embeddings_np.shape}")
