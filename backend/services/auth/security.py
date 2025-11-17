"""
Security utilities for authentication.

Handles password hashing with bcrypt, JWT token generation and verification,
and token blacklisting via Redis.
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

# Password hashing configuration (bcrypt with cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that a token is of the expected type (access or refresh).

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        True if token type matches, False otherwise
    """
    try:
        payload = decode_token(token)
        return payload.get("type") == expected_type
    except JWTError:
        return False


def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from a JWT token.

    Args:
        token: JWT token string

    Returns:
        User UUID if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id:
            return UUID(user_id)
        return None
    except (JWTError, ValueError):
        return None


def hash_token_for_storage(token: str) -> str:
    """
    Hash a token for secure storage in database.

    Uses SHA-256 to hash tokens before storing in database,
    preventing token theft from database dumps.

    Args:
        token: Token string to hash

    Returns:
        Hashed token string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_password_reset_token(user_id: UUID) -> str:
    """
    Generate a password reset token with 1-hour expiration.

    Args:
        user_id: User UUID

    Returns:
        Encoded password reset token
    """
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "password_reset"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_email_verification_token(user_id: UUID) -> str:
    """
    Generate an email verification token with 24-hour expiration.

    Args:
        user_id: User UUID

    Returns:
        Encoded email verification token
    """
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "email_verification"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[UUID]:
    """
    Verify a password reset token and extract user ID.

    Args:
        token: Password reset token

    Returns:
        User UUID if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            return None
        user_id = payload.get("sub")
        if user_id:
            return UUID(user_id)
        return None
    except (JWTError, ValueError):
        return None


def verify_email_verification_token(token: str) -> Optional[UUID]:
    """
    Verify an email verification token and extract user ID.

    Args:
        token: Email verification token

    Returns:
        User UUID if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "email_verification":
            return None
        user_id = payload.get("sub")
        if user_id:
            return UUID(user_id)
        return None
    except (JWTError, ValueError):
        return None
