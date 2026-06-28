from sentence_transformers import SentenceTransformer
from .settings import MODEL_NAME

print("Loading AI model...")

model = SentenceTransformer(MODEL_NAME)

print("AI model loaded.")
