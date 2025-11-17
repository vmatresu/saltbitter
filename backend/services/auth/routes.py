"""
Authentication routes for user registration, login, and token management.

Handles all authentication-related endpoints including registration, login,
token refresh, logout, password reset, and email verification.
"""

import os
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import RefreshToken, User
from .schemas import (
    AuthResponse,
    EmailVerificationRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from .security import (
    create_access_token,
    create_refresh_token,
    generate_email_verification_token,
    generate_password_reset_token,
    get_user_id_from_token,
    hash_password,
    hash_token_for_storage,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
    verify_token_type,
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_dev")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_db() -> Session:
    """
    Database session dependency.

    Yields:
        SQLAlchemy database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from access token.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if not verify_token_type(token, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """
    Register a new user account.

    Creates a new user with hashed password and sends email verification link.

    Args:
        request: Registration request with email and password
        db: Database session

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If email already registered
    """
    # Check if user already exists
    existing_user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password and create user
    hashed_pw = hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_pw,
        verified=False,  # Email verification required
        subscription_tier="free",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate email verification token
    verification_token = generate_email_verification_token(new_user.id)

    # TODO: Send verification email (integrate with email service)
    # For now, log the token (in production, send via email)
    print(f"Email verification token for {new_user.email}: {verification_token}")

    # Generate authentication tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    # Store refresh token in database
    token_hash = hash_token_for_storage(refresh_token)
    refresh_token_record = RefreshToken(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
    )
    db.add(refresh_token_record)
    db.commit()

    # Return response
    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,  # 15 minutes
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """
    Login with email and password.

    Authenticates user and returns access/refresh tokens.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store refresh token
    token_hash = hash_token_for_storage(refresh_token)
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
    )
    db.add(refresh_token_record)
    db.commit()

    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Validates refresh token and issues new access token.

    Args:
        request: Token refresh request with refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid or revoked
    """
    # Verify token type
    if not verify_token_type(request.refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Get user ID from token
    user_id = get_user_id_from_token(request.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Check if token is in database and not revoked
    token_hash = hash_token_for_storage(request.refresh_token)
    stored_token = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
    ).scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found or revoked",
        )

    # Check if token is expired
    if stored_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    # Generate new tokens
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_id)})

    # Revoke old refresh token
    stored_token.revoked = True
    stored_token.revoked_at = datetime.utcnow()

    # Store new refresh token
    new_token_hash = hash_token_for_storage(new_refresh_token)
    new_refresh_token_record = RefreshToken(
        user_id=user_id,
        token_hash=new_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
    )
    db.add(new_refresh_token_record)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=900,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: TokenRefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Logout user by revoking refresh token.

    Invalidates the provided refresh token to prevent future use.

    Args:
        request: Logout request with refresh token
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token not found
    """
    # Hash and find token
    token_hash = hash_token_for_storage(request.refresh_token)
    stored_token = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    # Revoke token
    stored_token.revoked = True
    stored_token.revoked_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Successfully logged out")


@router.post("/reset-password", response_model=MessageResponse)
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """
    Request password reset email.

    Sends password reset link to user's email.

    Args:
        request: Password reset request with email
        db: Database session

    Returns:
        Success message (always returns success to prevent email enumeration)
    """
    # Find user by email
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()

    if user:
        # Generate password reset token
        reset_token = generate_password_reset_token(user.id)

        # TODO: Send password reset email
        # For now, log the token (in production, send via email)
        print(f"Password reset token for {user.email}: {reset_token}")

    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a password reset link has been sent",
        detail="Check your email for instructions",
    )


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)) -> MessageResponse:
    """
    Confirm password reset with token.

    Resets user password using reset token.

    Args:
        request: Password reset confirmation with token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid
    """
    # Verify token and get user ID
    user_id = verify_password_reset_token(request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Find user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()

    # Revoke all existing refresh tokens for security
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,  # noqa: E712
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()

    return MessageResponse(
        message="Password reset successfully",
        detail="Please login with your new password",
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """
    Verify user email with verification token.

    Activates user account after email verification.

    Args:
        request: Email verification request with token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid
    """
    # Verify token and get user ID
    user_id = verify_email_verification_token(request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Find user
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Mark email as verified
    if user.verified:
        return MessageResponse(message="Email already verified")

    user.verified = True
    db.commit()

    return MessageResponse(
        message="Email verified successfully",
        detail="You can now access all features",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)
