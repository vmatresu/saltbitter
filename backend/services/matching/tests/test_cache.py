"""Tests for Redis caching in matching service."""

from uuid import uuid4

import pytest

from services.matching.cache import MatchCache


@pytest.fixture
async def cache():
    """Create cache instance for testing."""
    cache = MatchCache()
    await cache.connect()
    yield cache
    await cache.disconnect()


@pytest.mark.asyncio
async def test_set_and_get_user_matches(cache):
    """Test caching and retrieving user matches."""
    user_id = uuid4()
    matches = [
        {"user_id": str(uuid4()), "compatibility_score": 85.5, "status": "pending"},
        {"user_id": str(uuid4()), "compatibility_score": 92.0, "status": "pending"},
    ]

    # Set matches
    await cache.set_user_matches(user_id, matches)

    # Get matches
    cached_matches = await cache.get_user_matches(user_id)

    assert cached_matches is not None
    assert len(cached_matches) == 2
    assert cached_matches[0]["compatibility_score"] == 85.5


@pytest.mark.asyncio
async def test_get_user_matches_not_cached(cache):
    """Test retrieving non-existent cached matches."""
    user_id = uuid4()

    # Get matches that don't exist
    cached_matches = await cache.get_user_matches(user_id)

    assert cached_matches is None


@pytest.mark.asyncio
async def test_set_and_get_compatibility_score(cache):
    """Test caching and retrieving compatibility scores."""
    user_a_id = uuid4()
    user_b_id = uuid4()
    score = 87.5

    # Set score
    await cache.set_compatibility_score(user_a_id, user_b_id, score)

    # Get score
    cached_score = await cache.get_compatibility_score(user_a_id, user_b_id)

    assert cached_score is not None
    assert cached_score == 87.5


@pytest.mark.asyncio
async def test_get_compatibility_score_order_independent(cache):
    """Test that compatibility score can be retrieved regardless of user order."""
    user_a_id = uuid4()
    user_b_id = uuid4()
    score = 90.0

    # Set score with A, B order
    await cache.set_compatibility_score(user_a_id, user_b_id, score)

    # Get score with B, A order (should work)
    cached_score = await cache.get_compatibility_score(user_b_id, user_a_id)

    assert cached_score is not None
    assert cached_score == 90.0


@pytest.mark.asyncio
async def test_invalidate_user_matches(cache):
    """Test cache invalidation for user matches."""
    user_id = uuid4()
    matches = [
        {"user_id": str(uuid4()), "compatibility_score": 85.5, "status": "pending"},
    ]

    # Set matches
    await cache.set_user_matches(user_id, matches)

    # Verify they exist
    cached_matches = await cache.get_user_matches(user_id)
    assert cached_matches is not None

    # Invalidate
    await cache.invalidate_user_matches(user_id)

    # Verify they're gone
    cached_matches = await cache.get_user_matches(user_id)
    assert cached_matches is None


@pytest.mark.asyncio
async def test_set_and_get_user_preferences(cache):
    """Test caching and retrieving user preferences."""
    user_id = uuid4()
    preferences = {
        "gender": "female",
        "min_age": 25,
        "max_age": 35,
        "max_distance_km": 50,
    }

    # Set preferences
    await cache.set_user_preferences(user_id, preferences)

    # Get preferences
    cached_prefs = await cache.get_user_preferences(user_id)

    assert cached_prefs is not None
    assert cached_prefs["gender"] == "female"
    assert cached_prefs["min_age"] == 25


@pytest.mark.asyncio
async def test_invalidate_user_preferences(cache):
    """Test cache invalidation for user preferences."""
    user_id = uuid4()
    preferences = {"gender": "male"}

    # Set preferences
    await cache.set_user_preferences(user_id, preferences)

    # Verify they exist
    cached_prefs = await cache.get_user_preferences(user_id)
    assert cached_prefs is not None

    # Invalidate
    await cache.invalidate_user_preferences(user_id)

    # Verify they're gone
    cached_prefs = await cache.get_user_preferences(user_id)
    assert cached_prefs is None


@pytest.mark.asyncio
async def test_cache_key_generation(cache):
    """Test that cache keys are generated correctly."""
    user_id = uuid4()

    # User matches key
    matches_key = cache._user_matches_key(user_id)
    assert f"matches:user:{user_id}:daily" == matches_key

    # Compatibility key
    user_a = uuid4()
    user_b = uuid4()
    compat_key = cache._compatibility_key(user_a, user_b)
    assert "compatibility:" in compat_key
    assert str(user_a) in compat_key or str(user_b) in compat_key

    # Preferences key
    prefs_key = cache._user_preferences_key(user_id)
    assert f"preferences:user:{user_id}" == prefs_key


@pytest.mark.asyncio
async def test_cache_connection_reuse(cache):
    """Test that cache connection is reused."""
    user_id = uuid4()

    # First operation should create connection
    matches = [{"user_id": str(uuid4()), "compatibility_score": 80.0}]
    await cache.set_user_matches(user_id, matches)

    # Verify connection exists
    assert cache._redis is not None

    # Second operation should reuse connection
    cached = await cache.get_user_matches(user_id)
    assert cached is not None
