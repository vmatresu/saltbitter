"""
Authentication service module.

Provides authentication functionality including user registration, login,
token management, password reset, and email verification.
"""

from .routes import router as auth_router
from .schemas import (
    AuthResponse,
    TokenResponse,
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
)
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

__all__ = [
    "auth_router",
    "AuthResponse",
    "TokenResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
]
