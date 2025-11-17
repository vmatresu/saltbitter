"""
Interest and bio similarity using sentence embeddings.

This module uses sentence-transformers to calculate semantic similarity
between user bios, enabling interest-based matching beyond keyword matching.

Model: all-MiniLM-L6-v2
- 384-dimensional embeddings
- Fast inference (~50ms per bio)
- Good balance of quality and speed
"""

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

# Global model instance (loaded once, reused for all requests)
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get or initialize the sentence transformer model.

    Lazy-loads the model on first use to avoid startup overhead.
    Model is cached globally for subsequent requests.

    Returns:
        SentenceTransformer: The loaded model instance
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def generate_bio_embedding(bio_text: str) -> NDArray[np.float32]:
    """
    Generate embedding vector from user bio text.

    Converts bio text into a 384-dimensional semantic vector that captures
    the meaning and topics in the bio.

    Args:
        bio_text: User's bio text (can be empty)

    Returns:
        NDArray: 384-dimensional embedding vector (normalized)

    Examples:
        >>> embedding = generate_bio_embedding("I love hiking and photography")
        >>> embedding.shape
        (384,)
        >>> 0.99 <= np.linalg.norm(embedding) <= 1.01  # Normalized
        True
    """
    model = get_embedding_model()

    # Handle empty or None bios
    if not bio_text or bio_text.strip() == "":
        # Return zero vector for empty bios (will result in 0 similarity)
        return np.zeros(384, dtype=np.float32)

    # Generate embedding
    embedding = model.encode(bio_text, normalize_embeddings=True, show_progress_bar=False)

    return embedding.astype(np.float32)


def calculate_cosine_similarity(
    embedding_a: NDArray[np.float32], embedding_b: NDArray[np.float32]
) -> float:
    """
    Calculate cosine similarity between two embedding vectors.

    Cosine similarity ranges from -1 (opposite) to 1 (identical).
    For normalized vectors, this is simply the dot product.

    Args:
        embedding_a: First embedding vector (384-dim)
        embedding_b: Second embedding vector (384-dim)

    Returns:
        float: Cosine similarity (-1 to 1)

    Raises:
        ValueError: If embeddings have different dimensions

    Examples:
        >>> vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        >>> vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        >>> calculate_cosine_similarity(vec1, vec2)
        1.0
        >>> vec3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        >>> calculate_cosine_similarity(vec1, vec3)
        0.0
    """
    if embedding_a.shape != embedding_b.shape:
        raise ValueError(
            f"Embedding dimensions must match: {embedding_a.shape} != {embedding_b.shape}"
        )

    # For normalized vectors, cosine similarity = dot product
    similarity = float(np.dot(embedding_a, embedding_b))

    # Clamp to valid range (handle floating point errors)
    return np.clip(similarity, -1.0, 1.0)


def calculate_bio_similarity(bio_a: str, bio_b: str) -> float:
    """
    Calculate semantic similarity between two user bios.

    Returns a score from 0-100 based on the semantic similarity of the bios.
    Uses cosine similarity of sentence embeddings.

    Args:
        bio_a: First user's bio text
        bio_b: Second user's bio text

    Returns:
        float: Similarity score (0-100 scale)
            - 100: Very similar interests/values
            - 50: Moderately similar
            - 0: Very different

    Examples:
        >>> calculate_bio_similarity(
        ...     "I love hiking, camping, and outdoor adventures",
        ...     "Passionate about nature, hiking, and exploring the outdoors"
        ... )  # doctest: +SKIP
        85.0
        >>> calculate_bio_similarity(
        ...     "Software engineer who loves coding",
        ...     "Professional chef passionate about cooking"
        ... )  # doctest: +SKIP
        25.0
    """
    # Generate embeddings
    embedding_a = generate_bio_embedding(bio_a)
    embedding_b = generate_bio_embedding(bio_b)

    # Calculate similarity
    cosine_sim = calculate_cosine_similarity(embedding_a, embedding_b)

    # Convert from [-1, 1] to [0, 100] scale
    # We use (cosine_sim + 1) / 2 to map to [0, 1], then * 100 for [0, 100]
    similarity_score = ((cosine_sim + 1.0) / 2.0) * 100.0

    return float(similarity_score)


def batch_generate_embeddings(bio_texts: list[str]) -> list[NDArray[np.float32]]:
    """
    Generate embeddings for multiple bios efficiently.

    Uses batch processing for better performance when processing many bios.

    Args:
        bio_texts: List of bio texts

    Returns:
        list[NDArray]: List of 384-dimensional embedding vectors

    Examples:
        >>> bios = ["I love hiking", "I enjoy reading", "Passionate about coding"]
        >>> embeddings = batch_generate_embeddings(bios)
        >>> len(embeddings)
        3
        >>> embeddings[0].shape
        (384,)
    """
    model = get_embedding_model()

    # Handle empty bios
    processed_texts = [bio if bio and bio.strip() else "" for bio in bio_texts]

    # Batch encode (faster than individual encodes)
    embeddings = model.encode(
        processed_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=32,
    )

    # Replace empty bio embeddings with zero vectors
    result = []
    for i, (bio, emb) in enumerate(zip(bio_texts, embeddings)):
        if not bio or bio.strip() == "":
            result.append(np.zeros(384, dtype=np.float32))
        else:
            result.append(emb.astype(np.float32))

    return result
