"""
Matching service main module.

Provides high-level matching functions that can be called from API endpoints
or background tasks (Celery).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .algorithm import (
    CompatibilityScore,
    calculate_compatibility,
    fetch_user_match_profile,
    passes_preference_filters,
)


async def calculate_match_score(
    db: AsyncSession, user_a_id: UUID, user_b_id: UUID
) -> CompatibilityScore | None:
    """
    Calculate compatibility score between two users.

    Fetches user profiles and calculates multi-factor compatibility score.

    Args:
        db: Database session
        user_a_id: First user's ID
        user_b_id: Second user's ID

    Returns:
        CompatibilityScore if both users found and complete, None otherwise
    """
    # Fetch both user profiles
    user_a = await fetch_user_match_profile(db, user_a_id)
    user_b = await fetch_user_match_profile(db, user_b_id)

    if not user_a or not user_b:
        return None

    # Calculate compatibility
    score = calculate_compatibility(user_a, user_b)

    return score


async def check_users_compatible(
    db: AsyncSession, user_a_id: UUID, user_b_id: UUID
) -> bool:
    """
    Check if two users pass basic compatibility filters.

    Args:
        db: Database session
        user_a_id: First user's ID
        user_b_id: Second user's ID

    Returns:
        bool: True if users pass preference filters
    """
    # Fetch both user profiles
    user_a = await fetch_user_match_profile(db, user_a_id)
    user_b = await fetch_user_match_profile(db, user_b_id)

    if not user_a or not user_b:
        return False

    return passes_preference_filters(user_a, user_b)
