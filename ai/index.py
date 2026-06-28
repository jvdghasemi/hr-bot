import faiss
import numpy as np
import os

DATA_DIR = "data"
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")


def build_index(embeddings: np.ndarray):
    """
    Build and save a FAISS index.
    """

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    print(f"FAISS index saved: {INDEX_PATH}")


def load_index():
    """
    Load the saved FAISS index.
    """

    return faiss.read_index(INDEX_PATH)
