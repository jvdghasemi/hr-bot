from .model import model


def embed(text: str):
    """
    Convert text to embedding.
    """
    return model.encode(
        text,
        normalize_embeddings=True
    )
