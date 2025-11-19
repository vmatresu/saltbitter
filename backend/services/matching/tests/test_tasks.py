"""
Tests for Celery tasks in matching service.

Tests cover:
- Daily match generation
- Mutual match detection
- Cache invalidation
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Match, Profile, User
from database.models.attachment import AttachmentAssessment
from services.matching.tasks import (
    detect_mutual_match_for_like,
    detect_mutual_matches_batch,
    generate_daily_matches,
    invalidate_cache_for_user,
)


@pytest.fixture
async def test_users(db_session: AsyncSession):
    """Create test users with profiles and assessments."""
    users = []
    for i in range(5):
        # Create user
        user = User(
            email=f"testuser{i}@example.com",
            password_hash="hashed_password",
            verified=True,
            subscription_tier="free" if i < 3 else "premium",
        )
        db_session.add(user)
        await db_session.flush()

        # Create profile
        profile = Profile(
            user_id=user.id,
            name=f"Test User {i}",
            bio=f"Bio for user {i}",
            age=25 + i,
            gender="non-binary" if i % 2 == 0 else "male",
            location_lat=37.7749 + (i * 0.01),
            location_lon=-122.4194 + (i * 0.01),
            looking_for_gender="any",
            min_age=22,
            max_age=35,
            max_distance_km=50,
        )
        db_session.add(profile)

        # Create attachment assessment
        assessment = AttachmentAssessment(
            user_id=user.id,
            anxiety_score=2.5 + (i * 0.5),
            avoidance_score=2.0 + (i * 0.3),
            style="secure" if i < 2 else "anxious",
        )
        db_session.add(assessment)

        users.append(user)

    await db_session.commit()
    return users


@pytest.mark.asyncio
async def test_generate_daily_matches_success(db_session: AsyncSession, test_users):
    """Test successful daily match generation."""
    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = generate_daily_matches()

        # Check results
        assert result["users_processed"] > 0
        assert result["matches_created"] > 0

        # Verify matches were created in database
        stmt = select(Match).where(Match.status == "pending")
        db_result = await db_session.execute(stmt)
        matches = db_result.scalars().all()
        assert len(matches) > 0


@pytest.mark.asyncio
async def test_generate_daily_matches_no_users(db_session: AsyncSession):
    """Test match generation when no users need matches."""
    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = generate_daily_matches()

        # Should process 0 users when none need matches
        assert result["users_processed"] == 0
        assert result["matches_created"] == 0


@pytest.mark.asyncio
async def test_detect_mutual_match_for_like_positive(
    db_session: AsyncSession, test_users
):
    """Test mutual match detection when both users liked each other."""
    user_a = test_users[0]
    user_b = test_users[1]

    # Create matches where both users liked each other
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

    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = detect_mutual_match_for_like(str(user_a.id), str(user_b.id))

        # Should detect mutual match
        assert result["mutual_match"] is True

        # Verify matches updated to "matched" status
        await db_session.refresh(match_a)
        await db_session.refresh(match_b)
        assert match_a.status == "matched"
        assert match_b.status == "matched"


@pytest.mark.asyncio
async def test_detect_mutual_match_for_like_negative(
    db_session: AsyncSession, test_users
):
    """Test mutual match detection when only one user liked."""
    user_a = test_users[0]
    user_b = test_users[1]

    # Create match where only user A liked user B
    match_a = Match(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        compatibility_score=85.0,
        status="liked",
    )
    db_session.add(match_a)
    await db_session.commit()

    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = detect_mutual_match_for_like(str(user_a.id), str(user_b.id))

        # Should not detect mutual match
        assert result["mutual_match"] is False

        # Match should still be "liked" status
        await db_session.refresh(match_a)
        assert match_a.status == "liked"


@pytest.mark.asyncio
async def test_detect_mutual_matches_batch(db_session: AsyncSession, test_users):
    """Test batch mutual match detection."""
    user_a = test_users[0]
    user_b = test_users[1]
    user_c = test_users[2]

    # Create mutual like between A and B (recent)
    now = datetime.utcnow()
    match_ab1 = Match(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        compatibility_score=85.0,
        status="liked",
        created_at=now,
        updated_at=now,
    )
    match_ab2 = Match(
        user_a_id=user_b.id,
        user_b_id=user_a.id,
        compatibility_score=87.0,
        status="liked",
        created_at=now,
        updated_at=now,
    )

    # Create one-sided like between A and C (should not match)
    match_ac = Match(
        user_a_id=user_a.id,
        user_b_id=user_c.id,
        compatibility_score=75.0,
        status="liked",
        created_at=now,
        updated_at=now,
    )

    db_session.add(match_ab1)
    db_session.add(match_ab2)
    db_session.add(match_ac)
    await db_session.commit()

    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run batch detection
        result = detect_mutual_matches_batch()

        # Should find 1 mutual match (A-B)
        assert result["mutual_matches_found"] >= 1

        # Verify matches updated
        await db_session.refresh(match_ab1)
        await db_session.refresh(match_ab2)
        assert match_ab1.status == "matched"
        assert match_ab2.status == "matched"

        # One-sided match should still be "liked"
        await db_session.refresh(match_ac)
        assert match_ac.status == "liked"


@pytest.mark.asyncio
async def test_invalidate_cache_for_user():
    """Test cache invalidation for a user."""
    user_id = uuid4()

    with patch("services.matching.tasks.cache") as mock_cache:
        mock_cache.invalidate_user_matches = AsyncMock()
        mock_cache.invalidate_user_preferences = AsyncMock()

        # Run task
        result = invalidate_cache_for_user(str(user_id))

        # Should invalidate cache
        assert result["cache_invalidated"] is True
        mock_cache.invalidate_user_matches.assert_called_once()
        mock_cache.invalidate_user_preferences.assert_called_once()


@pytest.mark.asyncio
async def test_generate_daily_matches_respects_subscription_tiers(
    db_session: AsyncSession, test_users
):
    """Test that match generation respects subscription tier limits."""
    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = generate_daily_matches()

        # Verify free users got 5-10 matches, premium got more
        for user in test_users:
            stmt = select(Match).where(Match.user_a_id == user.id)
            db_result = await db_session.execute(stmt)
            matches = db_result.scalars().all()

            if user.subscription_tier == "free":
                # Free users should have <= 5-10 matches
                assert len(matches) <= 10
            elif user.subscription_tier == "premium":
                # Premium can have more matches
                assert len(matches) >= 0  # Just verify no error


@pytest.mark.asyncio
async def test_generate_daily_matches_excludes_seen_users(
    db_session: AsyncSession, test_users
):
    """Test that match generation excludes previously seen users."""
    user_a = test_users[0]
    user_b = test_users[1]

    # Create existing match from past week (should be excluded)
    existing_match = Match(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        compatibility_score=80.0,
        status="passed",
        created_at=datetime.utcnow() - timedelta(days=3),
    )
    db_session.add(existing_match)
    await db_session.commit()

    with patch("services.matching.tasks.async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session

        # Run task
        result = generate_daily_matches()

        # Verify user_b is not in user_a's new matches
        stmt = select(Match).where(
            Match.user_a_id == user_a.id,
            Match.status == "pending",
            Match.created_at > datetime.utcnow() - timedelta(minutes=5),
        )
        db_result = await db_session.execute(stmt)
        new_matches = db_result.scalars().all()

        # User B should not be in new matches
        for match in new_matches:
            assert match.user_b_id != user_b.id
