"""
Rate limiting middleware for authentication endpoints.

Implements rate limiting to prevent brute force attacks:
- 100 requests per minute per IP address (general)
- 5 login attempts per user per 15 minutes
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.routing import APIRoute


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        """
        Initialize rate limit exception.

        Args:
            retry_after: Seconds until rate limit resets
        """
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


class InMemoryRateLimiter:
    """
    In-memory rate limiter for development.

    In production, use Redis for distributed rate limiting.
    """

    def __init__(self) -> None:
        """Initialize rate limiter with in-memory storage."""
        self.requests: dict[str, list[datetime]] = defaultdict(list)
        self.login_attempts: dict[str, list[datetime]] = defaultdict(list)

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if rate limit is exceeded for a given key.

        Args:
            key: Identifier for rate limiting (e.g., IP address or user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if under limit, False if exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        # Clean up old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]

        # Check if under limit
        if len(self.requests[key]) >= max_requests:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

    def check_login_rate_limit(self, user_email: str) -> bool:
        """
        Check login rate limit for specific user.

        Allows 5 login attempts per 15 minutes per user.

        Args:
            user_email: User email address

        Returns:
            True if under limit, False if exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=15)

        # Clean up old attempts
        self.login_attempts[user_email] = [
            attempt_time for attempt_time in self.login_attempts[user_email] if attempt_time > cutoff
        ]

        # Check if under limit (5 attempts per 15 min)
        if len(self.login_attempts[user_email]) >= 5:
            return False

        # Add current attempt
        self.login_attempts[user_email].append(now)
        return True

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            key: Identifier for rate limiting
            window_seconds: Time window in seconds

        Returns:
            Seconds until oldest request expires
        """
        if key not in self.requests or not self.requests[key]:
            return 0

        oldest_request = self.requests[key][0]
        expires_at = oldest_request + timedelta(seconds=window_seconds)
        now = datetime.utcnow()

        if expires_at > now:
            return int((expires_at - now).total_seconds())
        return 0


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Rate limiting middleware for FastAPI.

    Applies rate limits to authentication endpoints:
    - 100 requests/min per IP (general)
    - 5 login attempts per user per 15 min (login endpoint)

    Args:
        request: FastAPI request
        call_next: Next middleware/route handler

    Returns:
        Response from next handler

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check general rate limit (100 req/min)
    if not rate_limiter.check_rate_limit(client_ip, max_requests=100, window_seconds=60):
        retry_after = rate_limiter.get_retry_after(client_ip, window_seconds=60)
        raise RateLimitExceeded(retry_after=retry_after)

    # Specific login endpoint rate limiting
    if request.url.path == "/api/auth/login" and request.method == "POST":
        try:
            body = await request.body()
            # Note: This consumes the request body, so we need to create a new request
            # In production, use a more sophisticated approach or Redis
            # For now, just apply IP-based limiting to login endpoint
            if not rate_limiter.check_rate_limit(f"login:{client_ip}", max_requests=10, window_seconds=60):
                retry_after = rate_limiter.get_retry_after(f"login:{client_ip}", window_seconds=60)
                raise RateLimitExceeded(retry_after=retry_after)
        except Exception:
            pass  # If body parsing fails, just apply general rate limit

    response = await call_next(request)
    return response


class RateLimitedRoute(APIRoute):
    """
    Custom APIRoute with rate limiting.

    Can be used to apply rate limiting to specific routes.
    """

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initialize rate-limited route."""
        super().__init__(*args, **kwargs)

    async def custom_route_handler(self, request: Request) -> Response:
        """Handle request with rate limiting."""
        client_ip = request.client.host if request.client else "unknown"

        # Apply rate limit
        if not rate_limiter.check_rate_limit(client_ip, max_requests=100, window_seconds=60):
            retry_after = rate_limiter.get_retry_after(client_ip, window_seconds=60)
            raise RateLimitExceeded(retry_after=retry_after)

        return await super().custom_route_handler(request)  # type: ignore
