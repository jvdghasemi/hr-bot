from sentence_transformers import SentenceTransformer
from .settings import MODEL_NAME

print(f"Loading AI model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print("AI model loaded.")
