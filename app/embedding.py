from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, logger

def get_model():
    """Load and return the sentence transformer model."""
    try:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Successfully loaded model with {model.get_sentence_embedding_dimension()} dimensions")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {str(e)}")
        raise
