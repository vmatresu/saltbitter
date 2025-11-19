"""
Match delivery logic for generating and delivering daily matches to users.

Handles:
- Fetching users needing matches
- Calculating compatibility scores
- Filtering seen/passed matches
- Delivering appropriate number of matches per tier
- Detecting mutual matches
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Match, Profile, User
from database.models.attachment import AttachmentAssessment

from .algorithm import calculate_compatibility, fetch_user_match_profile
from .cache import cache
from .notifications import notification_service

logger = logging.getLogger(__name__)


async def get_users_needing_matches(db: AsyncSession) -> list[UUID]:
    """
    Fetch users who need new matches.

    Users need matches if:
    - They don't have pending matches from today
    - Their profile is complete
    - They have completed attachment assessment

    Args:
        db: Database session

    Returns:
        List of user UUIDs needing matches
    """
    # Users who haven't received matches today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Find users with complete profiles and assessments
    stmt = (
        select(User.id)
        .join(Profile, Profile.user_id == User.id)
        .join(AttachmentAssessment, AttachmentAssessment.user_id == User.id)
        .where(
            and_(
                User.verified == True,  # noqa: E712
                Profile.name.isnot(None),
                AttachmentAssessment.style.isnot(None),
            )
        )
        .distinct()
    )

    result = await db.execute(stmt)
    user_ids = [row[0] for row in result.all()]

    # Filter out users who already have pending matches from today
    users_needing_matches = []
    for user_id in user_ids:
        stmt = select(Match.id).where(
            and_(
                or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
                Match.status == "pending",
                Match.created_at >= today_start,
            )
        ).limit(1)

        result = await db.execute(stmt)
        has_pending = result.scalar_one_or_none() is not None

        if not has_pending:
            users_needing_matches.append(user_id)

    logger.info(f"Found {len(users_needing_matches)} users needing new matches")
    return users_needing_matches


async def get_excluded_user_ids(db: AsyncSession, user_id: UUID) -> set[UUID]:
    """
    Get user IDs that should be excluded from matches.

    Excludes users who have been:
    - Previously matched (any status)
    - Seen in past 7 days

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        Set of excluded user UUIDs
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    stmt = select(Match.user_a_id, Match.user_b_id).where(
        and_(
            or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
            Match.created_at >= seven_days_ago,
        )
    )

    result = await db.execute(stmt)
    excluded = set()

    for user_a_id, user_b_id in result.all():
        if user_a_id == user_id:
            excluded.add(user_b_id)
        else:
            excluded.add(user_a_id)

    return excluded


async def calculate_potential_matches(
    db: AsyncSession, user_id: UUID, limit: int = 50
) -> list[tuple[UUID, float]]:
    """
    Calculate potential matches for a user with compatibility scores.

    Args:
        db: Database session
        user_id: User's UUID
        limit: Maximum number of potential matches to calculate

    Returns:
        List of tuples (user_id, compatibility_score), sorted by score descending
    """
    # Get excluded users
    excluded_ids = await get_excluded_user_ids(db, user_id)
    excluded_ids.add(user_id)  # Don't match with self

    # Get user's profile
    user_profile = await fetch_user_match_profile(db, user_id)
    if not user_profile:
        logger.warning(f"Could not fetch profile for user {user_id}")
        return []

    # Find potential matches (users with complete profiles)
    stmt = (
        select(User.id)
        .join(Profile, Profile.user_id == User.id)
        .join(AttachmentAssessment, AttachmentAssessment.user_id == User.id)
        .where(
            and_(
                User.id.notin_(excluded_ids),
                User.verified == True,  # noqa: E712
                Profile.name.isnot(None),
                AttachmentAssessment.style.isnot(None),
            )
        )
        .limit(limit)
    )

    result = await db.execute(stmt)
    potential_user_ids = [row[0] for row in result.all()]

    # Calculate compatibility scores
    scored_matches = []
    for potential_user_id in potential_user_ids:
        # Check cache first
        cached_score = await cache.get_compatibility_score(user_id, potential_user_id)
        if cached_score is not None:
            scored_matches.append((potential_user_id, cached_score))
            continue

        # Calculate and cache score
        potential_profile = await fetch_user_match_profile(db, potential_user_id)
        if potential_profile:
            compatibility = calculate_compatibility(user_profile, potential_profile)
            score = compatibility.total_score

            # Cache the score
            await cache.set_compatibility_score(user_id, potential_user_id, score)
            scored_matches.append((potential_user_id, score))

    # Sort by score descending
    scored_matches.sort(key=lambda x: x[1], reverse=True)

    return scored_matches


async def deliver_matches_to_user(
    db: AsyncSession, user_id: UUID
) -> int:
    """
    Generate and deliver daily matches to a specific user.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        Number of matches delivered
    """
    # Get user's subscription tier
    stmt = select(User.subscription_tier).where(User.id == user_id)
    result = await db.execute(stmt)
    tier = result.scalar_one_or_none()

    if not tier:
        logger.warning(f"User {user_id} not found")
        return 0

    # Determine number of matches based on tier
    if tier == "free":
        num_matches = 5  # Free tier gets 5-10 matches
    elif tier == "premium":
        num_matches = 20  # Premium gets more matches
    elif tier == "elite":
        num_matches = 50  # Elite gets unlimited (capped at 50 for performance)
    else:
        num_matches = 5

    # Calculate potential matches
    potential_matches = await calculate_potential_matches(db, user_id, limit=num_matches * 2)

    if not potential_matches:
        logger.info(f"No potential matches found for user {user_id}")
        return 0

    # Take top N matches
    top_matches = potential_matches[:num_matches]

    # Create Match records
    matches_created = []
    for match_user_id, compatibility_score in top_matches:
        match = Match(
            user_a_id=user_id,
            user_b_id=match_user_id,
            compatibility_score=compatibility_score,
            status="pending",
        )
        db.add(match)
        matches_created.append(
            {
                "user_id": str(match_user_id),
                "compatibility_score": compatibility_score,
                "status": "pending",
            }
        )

    await db.commit()

    # Cache the matches
    await cache.set_user_matches(user_id, matches_created)

    # Send notification
    await notification_service.send_new_matches_notification(user_id, len(matches_created))

    logger.info(f"Delivered {len(matches_created)} matches to user {user_id}")
    return len(matches_created)


async def detect_mutual_match(
    db: AsyncSession, user_a_id: UUID, user_b_id: UUID
) -> bool:
    """
    Check if two users have mutually liked each other.

    Args:
        db: Database session
        user_a_id: First user's UUID
        user_b_id: Second user's UUID

    Returns:
        bool: True if mutual match detected and updated
    """
    # Check if user A liked user B
    stmt_a = select(Match.id, Match.status).where(
        and_(
            Match.user_a_id == user_a_id,
            Match.user_b_id == user_b_id,
        )
    )
    result_a = await db.execute(stmt_a)
    match_a = result_a.first()

    # Check if user B liked user A
    stmt_b = select(Match.id, Match.status).where(
        and_(
            Match.user_a_id == user_b_id,
            Match.user_b_id == user_a_id,
        )
    )
    result_b = await db.execute(stmt_b)
    match_b = result_b.first()

    # If both exist and both are "liked", it's a mutual match
    if match_a and match_b and match_a[1] == "liked" and match_b[1] == "liked":
        # Update both to "matched" status
        stmt_update_a = (
            select(Match).where(Match.id == match_a[0])
        )
        result = await db.execute(stmt_update_a)
        match_obj_a = result.scalar_one()
        match_obj_a.status = "matched"

        stmt_update_b = (
            select(Match).where(Match.id == match_b[0])
        )
        result = await db.execute(stmt_update_b)
        match_obj_b = result.scalar_one()
        match_obj_b.status = "matched"

        await db.commit()

        # Send notifications to both users
        # Get user names for notifications
        stmt_name_a = select(Profile.name).where(Profile.user_id == user_a_id)
        result = await db.execute(stmt_name_a)
        name_a = result.scalar_one_or_none() or "Someone"

        stmt_name_b = select(Profile.name).where(Profile.user_id == user_b_id)
        result = await db.execute(stmt_name_b)
        name_b = result.scalar_one_or_none() or "Someone"

        await notification_service.send_mutual_match_notification(user_a_id, user_b_id, name_b)
        await notification_service.send_mutual_match_notification(user_b_id, user_a_id, name_a)

        logger.info(f"Mutual match detected: {user_a_id} ↔ {user_b_id}")
        return True

    return False
