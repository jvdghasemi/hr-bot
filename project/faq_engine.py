# faq_engine.py

import numpy as np
from sentence_transformers import SentenceTransformer, util
from config import SIMILARITY_THRESHOLD
from database import cursor

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

faq_cache = []


def load_faq_cache():
    global faq_cache

    cursor.execute("SELECT category, content, embedding FROM faq")
    rows = cursor.fetchall()

    faq_cache = []

    for category, content, emb in rows:
        faq_cache.append({
            "category": category,
            "content": content,
            "vector": np.frombuffer(emb, dtype=np.float32)
        })


def find_best_faq(text):
    if not faq_cache:
        load_faq_cache()

    text_vec = model.encode(text)

    best_score = -1
    best_answer = None

    for item in faq_cache:
        score = util.cos_sim(text_vec, item["vector"]).item()

        if score > best_score:
            best_score = score
            best_answer = item

    if best_score >= SIMILARITY_THRESHOLD:
        return best_answer

    return None
