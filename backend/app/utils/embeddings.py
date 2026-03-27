"""Embedding generation for graph memory vector search.

Uses Voyage AI for production embeddings. Falls back to zero-vector
when API key is unavailable (system works without embeddings, just
loses vector similarity search).
"""

from typing import List, Optional

from ..config import Config
from .logger import get_logger

logger = get_logger('foresight.embeddings')

EMBEDDING_DIM = 1024  # voyage-3-lite dimension


def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """Generate embedding vector for text.

    Returns list of floats (1024-dim for voyage-3-lite).
    Falls back to zero-vector if API unavailable.
    """
    api_key = Config.EMBEDDING_API_KEY or Config.CLAUDE_API_KEY
    model = model or Config.EMBEDDING_MODEL

    if not api_key:
        logger.debug("No embedding API key configured, returning zero vector")
        return [0.0] * EMBEDDING_DIM

    try:
        import voyageai
        client = voyageai.Client(api_key=api_key)
        result = client.embed([text], model=model)
        return result.embeddings[0]
    except ImportError:
        logger.warning("voyageai not installed, returning zero vector")
        return [0.0] * EMBEDDING_DIM
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return [0.0] * EMBEDDING_DIM
