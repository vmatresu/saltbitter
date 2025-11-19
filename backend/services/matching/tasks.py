"""
Celery tasks for match generation and mutual match detection.

Tasks:
- generate_daily_matches: Scheduled task to generate matches for all users
- detect_mutual_matches: Check for mutual matches after like actions
- detect_mutual_matches_batch: Periodic batch check for mutual matches
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Match

from .celery_app import app
from .match_delivery import (
    deliver_matches_to_user,
    detect_mutual_match,
    get_users_needing_matches,
)

logger = logging.getLogger(__name__)

# Database configuration (will be injected via environment in production)
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/saltbitter"
)

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def _get_db_session() -> AsyncSession:
    """Get database session for async operations."""
    return async_session_factory()


@app.task(name="services.matching.tasks.generate_daily_matches")
def generate_daily_matches() -> dict:
    """
    Generate daily matches for all users needing them.

    This task:
    1. Finds users needing new matches
    2. Generates matches for each user
    3. Caches results in Redis
    4. Sends push notifications

    Returns:
        dict: Stats including users_processed, matches_created
    """
    logger.info("Starting daily match generation")

    async def _generate() -> dict:
        async with async_session_factory() as db:
            # Get users needing matches
            user_ids = await get_users_needing_matches(db)

            if not user_ids:
                logger.info("No users need matches")
                return {"users_processed": 0, "matches_created": 0}

            # Generate matches for each user
            total_matches = 0
            users_processed = 0

            for user_id in user_ids:
                try:
                    matches_created = await deliver_matches_to_user(db, user_id)
                    total_matches += matches_created
                    users_processed += 1
                    logger.info(
                        f"Delivered {matches_created} matches to user {user_id}"
                    )
                except Exception as e:
                    logger.error(f"Error generating matches for user {user_id}: {e}")
                    continue

            logger.info(
                f"Daily match generation complete: "
                f"{users_processed} users processed, "
                f"{total_matches} matches created"
            )

            return {
                "users_processed": users_processed,
                "matches_created": total_matches,
            }

    # Run async function in event loop
    return asyncio.run(_generate())


@app.task(name="services.matching.tasks.detect_mutual_match_for_like")
def detect_mutual_match_for_like(user_a_id: str, user_b_id: str) -> dict:
    """
    Check if a like action created a mutual match.

    Called after a user likes another user's profile.

    Args:
        user_a_id: User who liked (UUID string)
        user_b_id: User who was liked (UUID string)

    Returns:
        dict: {"mutual_match": bool}
    """
    async def _detect() -> dict:
        async with async_session_factory() as db:
            is_mutual = await detect_mutual_match(
                db, UUID(user_a_id), UUID(user_b_id)
            )
            return {"mutual_match": is_mutual}

    return asyncio.run(_detect())


@app.task(name="services.matching.tasks.detect_mutual_matches_batch")
def detect_mutual_matches_batch() -> dict:
    """
    Periodic batch check for mutual matches.

    Scans recent "liked" matches to detect mutual matches that
    might have been missed.

    Returns:
        dict: {"mutual_matches_found": int}
    """
    logger.info("Starting batch mutual match detection")

    async def _detect_batch() -> dict:
        async with async_session_factory() as db:
            # Find all "liked" matches from the past hour
            from datetime import datetime, timedelta

            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            stmt = select(Match).where(
                and_(Match.status == "liked", Match.updated_at >= one_hour_ago)
            )

            result = await db.execute(stmt)
            liked_matches = result.scalars().all()

            mutual_matches_found = 0

            for match in liked_matches:
                try:
                    is_mutual = await detect_mutual_match(
                        db, match.user_a_id, match.user_b_id
                    )
                    if is_mutual:
                        mutual_matches_found += 1
                except Exception as e:
                    logger.error(
                        f"Error detecting mutual match for {match.id}: {e}"
                    )
                    continue

            logger.info(f"Batch detection complete: {mutual_matches_found} mutual matches found")

            return {"mutual_matches_found": mutual_matches_found}

    return asyncio.run(_detect_batch())


@app.task(name="services.matching.tasks.invalidate_cache_for_user")
def invalidate_cache_for_user(user_id: str) -> dict:
    """
    Invalidate cached matches for a user (e.g., after profile update).

    Args:
        user_id: User's UUID string

    Returns:
        dict: {"cache_invalidated": bool}
    """
    from .cache import cache

    async def _invalidate() -> dict:
        await cache.invalidate_user_matches(UUID(user_id))
        await cache.invalidate_user_preferences(UUID(user_id))
        return {"cache_invalidated": True}

    return asyncio.run(_invalidate())
