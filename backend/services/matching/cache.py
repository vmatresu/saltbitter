"""
Redis caching for match results and compatibility scores.

Implements caching strategy:
- Match results: 24h TTL
- Compatibility scores: 168h (1 week) TTL
- User preferences: 6h TTL
"""

import json
import os
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cache TTLs in seconds
MATCH_RESULTS_TTL = 24 * 3600  # 24 hours
COMPATIBILITY_SCORES_TTL = 168 * 3600  # 1 week
USER_PREFERENCES_TTL = 6 * 3600  # 6 hours


class MatchCache:
    """Redis cache manager for matching service."""

    def __init__(self, redis_url: str = REDIS_URL):
        """
        Initialize cache with Redis connection.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        if not self._redis:
            self._redis = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _user_matches_key(self, user_id: UUID) -> str:
        """
        Generate cache key for user's daily matches.

        Args:
            user_id: User's UUID

        Returns:
            Cache key string
        """
        return f"matches:user:{user_id}:daily"

    def _compatibility_key(self, user_a_id: UUID, user_b_id: UUID) -> str:
        """
        Generate cache key for compatibility score between two users.

        Args:
            user_a_id: First user's UUID
            user_b_id: Second user's UUID

        Returns:
            Cache key string
        """
        # Sort UUIDs to ensure consistent key regardless of order
        sorted_ids = sorted([str(user_a_id), str(user_b_id)])
        return f"compatibility:{sorted_ids[0]}:{sorted_ids[1]}"

    def _user_preferences_key(self, user_id: UUID) -> str:
        """
        Generate cache key for user preferences.

        Args:
            user_id: User's UUID

        Returns:
            Cache key string
        """
        return f"preferences:user:{user_id}"

    async def get_user_matches(self, user_id: UUID) -> list[dict[str, Any]] | None:
        """
        Get cached daily matches for a user.

        Args:
            user_id: User's UUID

        Returns:
            List of match dictionaries, or None if not cached
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_matches_key(user_id)
        data = await self._redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_user_matches(
        self, user_id: UUID, matches: list[dict[str, Any]]
    ) -> None:
        """
        Cache daily matches for a user.

        Args:
            user_id: User's UUID
            matches: List of match dictionaries
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_matches_key(user_id)
        data = json.dumps(matches, default=str)
        await self._redis.setex(key, MATCH_RESULTS_TTL, data)

    async def get_compatibility_score(
        self, user_a_id: UUID, user_b_id: UUID
    ) -> float | None:
        """
        Get cached compatibility score between two users.

        Args:
            user_a_id: First user's UUID
            user_b_id: Second user's UUID

        Returns:
            Compatibility score (0-100), or None if not cached
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._compatibility_key(user_a_id, user_b_id)
        score = await self._redis.get(key)

        if score:
            return float(score)
        return None

    async def set_compatibility_score(
        self, user_a_id: UUID, user_b_id: UUID, score: float
    ) -> None:
        """
        Cache compatibility score between two users.

        Args:
            user_a_id: First user's UUID
            user_b_id: Second user's UUID
            score: Compatibility score (0-100)
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._compatibility_key(user_a_id, user_b_id)
        await self._redis.setex(key, COMPATIBILITY_SCORES_TTL, str(score))

    async def invalidate_user_matches(self, user_id: UUID) -> None:
        """
        Invalidate cached matches for a user (e.g., on profile update).

        Args:
            user_id: User's UUID
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_matches_key(user_id)
        await self._redis.delete(key)

    async def invalidate_user_preferences(self, user_id: UUID) -> None:
        """
        Invalidate cached preferences for a user.

        Args:
            user_id: User's UUID
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_preferences_key(user_id)
        await self._redis.delete(key)

    async def get_user_preferences(self, user_id: UUID) -> dict[str, Any] | None:
        """
        Get cached user preferences.

        Args:
            user_id: User's UUID

        Returns:
            Preferences dictionary, or None if not cached
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_preferences_key(user_id)
        data = await self._redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_user_preferences(
        self, user_id: UUID, preferences: dict[str, Any]
    ) -> None:
        """
        Cache user preferences.

        Args:
            user_id: User's UUID
            preferences: Preferences dictionary
        """
        if not self._redis:
            await self.connect()

        assert self._redis is not None
        key = self._user_preferences_key(user_id)
        data = json.dumps(preferences, default=str)
        await self._redis.setex(key, USER_PREFERENCES_TTL, data)


# Global cache instance
cache = MatchCache()
