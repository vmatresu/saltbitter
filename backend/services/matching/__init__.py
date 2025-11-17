"""
Matching service package.

Provides multi-factor compatibility matching algorithm combining:
- Attachment theory compatibility (40%)
- Location proximity (20%)
- Interest similarity (20%)
- Age preferences (10%)
- Other preferences (10%)
"""

from .algorithm import (
    CompatibilityScore,
    UserMatchProfile,
    calculate_compatibility,
    passes_preference_filters,
)
from .compatibility import (
    calculate_attachment_compatibility,
    calculate_attachment_compatibility_from_scores,
    determine_attachment_style,
)
from .embeddings import calculate_bio_similarity, generate_bio_embedding
from .main import calculate_match_score, check_users_compatible

__all__ = [
    # Algorithm
    "CompatibilityScore",
    "UserMatchProfile",
    "calculate_compatibility",
    "passes_preference_filters",
    # Compatibility
    "calculate_attachment_compatibility",
    "calculate_attachment_compatibility_from_scores",
    "determine_attachment_style",
    # Embeddings
    "calculate_bio_similarity",
    "generate_bio_embedding",
    # Main service
    "calculate_match_score",
    "check_users_compatible",
]
