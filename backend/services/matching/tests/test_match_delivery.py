"""Tests for match delivery logic."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Match, Profile, User
from database.models.attachment import AttachmentAssessment
from services.matching.match_delivery import (
    calculate_potential_matches,
    deliver_matches_to_user,
    detect_mutual_match,
    get_excluded_user_ids,
    get_users_needing_matches,
)


@pytest.fixture
async def test_users_with_profiles(db_session: AsyncSession):
    """Create test users with complete profiles."""
    users = []
    for i in range(5):
        # Create user
        user = User(
            email=f"user{i}@test.com",
            password_hash="hashed",
            verified=True,
            subscription_tier="free" if i < 3 else "premium",
        )
        db_session.add(user)
        await db_session.flush()

        # Create profile
        profile = Profile(
            user_id=user.id,
            name=f"User {i}",
            bio=f"Test bio {i}",
            age=25 + i,
            gender="non-binary" if i % 2 else "female",
            location_lat=37.7 + (i * 0.01),
            location_lon=-122.4 + (i * 0.01),
            looking_for_gender="any",
            min_age=22,
            max_age=35,
            max_distance_km=50,
        )
        db_session.add(profile)

        # Create assessment
        assessment = AttachmentAssessment(
            user_id=user.id,
            anxiety_score=2.5,
            avoidance_score=2.0,
            style="secure",
        )
        db_session.add(assessment)

        users.append(user)

    await db_session.commit()
    return users


@pytest.mark.asyncio
async def test_get_users_needing_matches_empty_db(db_session: AsyncSession):
    """Test getting users when database is empty."""
    user_ids = await get_users_needing_matches(db_session)
    assert user_ids == []


@pytest.mark.asyncio
async def test_get_users_needing_matches_with_users(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test getting users who need matches."""
    user_ids = await get_users_needing_matches(db_session)

    # All test users should need matches initially
    assert len(user_ids) == len(test_users_with_profiles)
    for user in test_users_with_profiles:
        assert user.id in user_ids


@pytest.mark.asyncio
async def test_get_users_needing_matches_excludes_with_pending(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test that users with pending matches today are excluded."""
    user = test_users_with_profiles[0]
    other_user = test_users_with_profiles[1]

    # Create pending match for user
    match = Match(
        user_a_id=user.id,
        user_b_id=other_user.id,
        compatibility_score=85.0,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db_session.add(match)
    await db_session.commit()

    # Get users needing matches
    user_ids = await get_users_needing_matches(db_session)

    # User with pending match should be excluded
    assert user.id not in user_ids


@pytest.mark.asyncio
async def test_get_excluded_user_ids_empty(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test getting excluded users when there are none."""
    user = test_users_with_profiles[0]

    excluded = await get_excluded_user_ids(db_session, user.id)

    assert len(excluded) == 0


@pytest.mark.asyncio
async def test_get_excluded_user_ids_with_matches(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test getting excluded users based on match history."""
    user = test_users_with_profiles[0]
    matched_user_1 = test_users_with_profiles[1]
    matched_user_2 = test_users_with_profiles[2]

    # Create matches from past 7 days
    match1 = Match(
        user_a_id=user.id,
        user_b_id=matched_user_1.id,
        compatibility_score=80.0,
        status="passed",
        created_at=datetime.utcnow() - timedelta(days=3),
    )
    match2 = Match(
        user_a_id=matched_user_2.id,
        user_b_id=user.id,
        compatibility_score=75.0,
        status="liked",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    db_session.add(match1)
    db_session.add(match2)
    await db_session.commit()

    # Get excluded users
    excluded = await get_excluded_user_ids(db_session, user.id)

    # Both matched users should be excluded
    assert matched_user_1.id in excluded
    assert matched_user_2.id in excluded


@pytest.mark.asyncio
async def test_calculate_potential_matches(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test calculating potential matches for a user."""
    user = test_users_with_profiles[0]

    # Calculate potential matches
    matches = await calculate_potential_matches(db_session, user.id, limit=10)

    # Should find some potential matches
    assert len(matches) > 0

    # Each match should be a tuple of (user_id, score)
    for user_id, score in matches:
        assert isinstance(user_id, type(user.id))
        assert 0 <= score <= 100

    # Matches should be sorted by score descending
    scores = [score for _, score in matches]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_calculate_potential_matches_excludes_self(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test that potential matches don't include the user themselves."""
    user = test_users_with_profiles[0]

    matches = await calculate_potential_matches(db_session, user.id)

    # User should not be in their own matches
    match_user_ids = [user_id for user_id, _ in matches]
    assert user.id not in match_user_ids


@pytest.mark.asyncio
async def test_deliver_matches_to_user_free_tier(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test delivering matches to a free tier user."""
    user = test_users_with_profiles[0]  # Free tier
    assert user.subscription_tier == "free"

    # Deliver matches
    count = await deliver_matches_to_user(db_session, user.id)

    # Should deliver some matches
    assert count > 0
    assert count <= 5  # Free tier limit

    # Verify matches in database
    stmt = select(Match).where(Match.user_a_id == user.id)
    result = await db_session.execute(stmt)
    matches = result.scalars().all()
    assert len(matches) == count


@pytest.mark.asyncio
async def test_deliver_matches_to_user_premium_tier(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test delivering matches to a premium tier user."""
    user = test_users_with_profiles[3]  # Premium tier
    assert user.subscription_tier == "premium"

    # Deliver matches
    count = await deliver_matches_to_user(db_session, user.id)

    # Premium should get more matches
    assert count > 0

    # Verify matches in database
    stmt = select(Match).where(Match.user_a_id == user.id)
    result = await db_session.execute(stmt)
    matches = result.scalars().all()
    assert len(matches) == count


@pytest.mark.asyncio
async def test_detect_mutual_match_positive(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test detecting mutual match when both users liked each other."""
    user_a = test_users_with_profiles[0]
    user_b = test_users_with_profiles[1]

    # Create mutual likes
    match_a = Match(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        compatibility_score=85.0,
        status="liked",
    )
    match_b = Match(
        user_a_id=user_b.id,
        user_b_id=user_a.id,
        compatibility_score=87.0,
        status="liked",
    )
    db_session.add(match_a)
    db_session.add(match_b)
    await db_session.commit()

    # Detect mutual match
    is_mutual = await detect_mutual_match(db_session, user_a.id, user_b.id)

    assert is_mutual is True

    # Verify matches updated to "matched"
    await db_session.refresh(match_a)
    await db_session.refresh(match_b)
    assert match_a.status == "matched"
    assert match_b.status == "matched"


@pytest.mark.asyncio
async def test_detect_mutual_match_negative(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test detecting mutual match when only one user liked."""
    user_a = test_users_with_profiles[0]
    user_b = test_users_with_profiles[1]

    # Create one-sided like
    match_a = Match(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        compatibility_score=85.0,
        status="liked",
    )
    db_session.add(match_a)
    await db_session.commit()

    # Detect mutual match
    is_mutual = await detect_mutual_match(db_session, user_a.id, user_b.id)

    assert is_mutual is False

    # Match should still be "liked"
    await db_session.refresh(match_a)
    assert match_a.status == "liked"


@pytest.mark.asyncio
async def test_deliver_matches_respects_exclusions(
    db_session: AsyncSession, test_users_with_profiles
):
    """Test that match delivery excludes previously seen users."""
    user = test_users_with_profiles[0]
    excluded_user = test_users_with_profiles[1]

    # Create past match
    past_match = Match(
        user_a_id=user.id,
        user_b_id=excluded_user.id,
        compatibility_score=75.0,
        status="passed",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    db_session.add(past_match)
    await db_session.commit()

    # Deliver new matches
    count = await deliver_matches_to_user(db_session, user.id)

    # Get new matches
    stmt = select(Match).where(
        Match.user_a_id == user.id,
        Match.created_at > datetime.utcnow() - timedelta(minutes=5),
    )
    result = await db_session.execute(stmt)
    new_matches = result.scalars().all()

    # Excluded user should not be in new matches
    for match in new_matches:
        assert match.user_b_id != excluded_user.id
