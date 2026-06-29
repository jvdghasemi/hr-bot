import time
import pickle
import os
import numpy as np
import faiss
from .model import model
from .settings import SIMILARITY_THRESHOLD, TOP_K, DATA_DIR


class SemanticSearch:
    def __init__(self):
        index_path = os.path.join(DATA_DIR, "faiss.index")
        docs_path = os.path.join(DATA_DIR, "documents.pkl")

        self.index = faiss.read_index(index_path)

        with open(docs_path, "rb") as f:
            self.documents = pickle.load(f)

        print(f"SemanticSearch ready: {len(self.documents)} documents loaded.")


def ask(self, text: str) -> dict | None:
    t0 = time.time()

    vector = model.encode(text, normalize_embeddings=True)
    print(f"[TIME] Encode: {time.time()-t0:.2f}s")

    t1 = time.time()

    vector = np.array(vector, dtype=np.float32).reshape(1, -1)
    scores, indices = self.index.search(vector, TOP_K)

    print(f"[TIME] Search: {time.time()-t1:.4f}s")

    score = float(scores[0][0])
    idx = int(indices[0][0])

    print(f"[AI] score={score:.3f}")

    if idx == -1 or score < SIMILARITY_THRESHOLD:
        return None

    return self.documents[idx]
