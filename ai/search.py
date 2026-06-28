import pickle
import numpy as np
from ai.settings import SIMILARITY_THRESHOLD
from ai.embedder import embed
from ai.index import load_index


class SemanticSearch:
    def __init__(self):
        self.index = load_index()

        with open("data/documents.pkl", "rb") as f:
            self.documents = pickle.load(f)

    def ask(self, text, top_k=1):
        vector = embed(text).astype(np.float32).reshape(1, -1)

        scores, indices = self.index.search(vector, top_k)

        score = float(scores[0][0])
        idx = int(indices[0][0])

        print(f"Score: {score}")

        if idx == -1:
            return None

        if score < SIMILARITY_THRESHOLD:
            return None

        return self.documents[idx]
