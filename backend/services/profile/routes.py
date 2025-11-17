"""
Profile management routes.

Handles profile CRUD operations, photo uploads/deletions,
and profile completeness calculations.
"""

import os
from datetime import datetime
from typing import Annotated, Any, Generator
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile, status
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Profile, User
from .schemas import (
    PhotoDeleteResponse,
    PhotoInfo,
    PhotoUploadResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from .storage import storage_service

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_dev")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create router
router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields:
        SQLAlchemy database session
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
    # Import here to avoid circular dependency
    from backend.services.auth.security import get_user_id_from_token, verify_token_type

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
    user = db.get(User, UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def calculate_completeness_score(profile: Profile) -> float:
    """
    Calculate profile completeness score (0-100%).

    Args:
        profile: Profile model instance

    Returns:
        Completeness score as percentage
    """
    score = 0.0
    total_weight = 100.0

    # Required fields (already have: name, age, gender) - 30 points
    score += 30.0

    # Bio - 20 points
    if profile.bio and len(profile.bio.strip()) > 0:
        score += 20.0

    # Location - 15 points
    if profile.location is not None:
        score += 15.0

    # Photos - 25 points (5 points per photo, max 5 photos counted)
    if profile.photos:
        photos_list = profile.photos if isinstance(profile.photos, list) else []
        num_photos = min(len(photos_list), 5)
        score += num_photos * 5.0

    # Preferences - 10 points (2 points each)
    if profile.looking_for_gender:
        score += 2.0
    if profile.min_age is not None:
        score += 2.0
    if profile.max_age is not None:
        score += 2.0
    if profile.max_distance_km is not None:
        score += 4.0

    return min(score, total_weight)


def parse_location(location_wkb: Any) -> dict[str, float] | None:
    """
    Parse PostGIS location to lat/lng dict.

    Args:
        location_wkb: PostGIS GEOGRAPHY object

    Returns:
        Dictionary with lat and lng, or None
    """
    if location_wkb is None:
        return None

    try:
        point = to_shape(location_wkb)
        return {"lat": point.y, "lng": point.x}
    except Exception:
        return None


def parse_photos(photos_json: Any) -> list[PhotoInfo]:
    """
    Parse photos JSON to PhotoInfo list.

    Args:
        photos_json: JSONB photos field from database

    Returns:
        List of PhotoInfo objects
    """
    if not photos_json:
        return []

    try:
        photos_list = photos_json if isinstance(photos_json, list) else []
        return [
            PhotoInfo(
                photo_id=photo.get("photo_id", ""),
                url=photo.get("url", ""),
                uploaded_at=datetime.fromisoformat(photo.get("uploaded_at", datetime.utcnow().isoformat())),
                order=photo.get("order", idx),
            )
            for idx, photo in enumerate(photos_list)
        ]
    except Exception:
        return []


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """
    Get user profile by ID.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Profile information

    Raises:
        HTTPException: If profile not found
    """
    profile = db.get(Profile, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Parse location
    location = parse_location(profile.location)

    # Parse photos
    photos = parse_photos(profile.photos)

    return ProfileResponse(
        user_id=profile.user_id,
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        bio=profile.bio,
        photos=photos,
        location=location,
        completeness_score=profile.completeness_score,
        looking_for_gender=profile.looking_for_gender,
        min_age=profile.min_age,
        max_age=profile.max_age,
        max_distance_km=profile.max_distance_km,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: UUID,
    profile_update: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """
    Update user profile.

    Args:
        user_id: User UUID
        profile_update: Profile update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated profile information

    Raises:
        HTTPException: If profile not found or user not authorized
    """
    # Check authorization - users can only update their own profile
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this profile")

    profile = db.get(Profile, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Update fields if provided
    if profile_update.name is not None:
        profile.name = profile_update.name
    if profile_update.age is not None:
        profile.age = profile_update.age
    if profile_update.gender is not None:
        profile.gender = profile_update.gender
    if profile_update.bio is not None:
        profile.bio = profile_update.bio
    if profile_update.location is not None:
        # Convert to PostGIS POINT
        point = Point(profile_update.location.longitude, profile_update.location.latitude)
        profile.location = func.ST_GeogFromText(f"POINT({point.x} {point.y})")
    if profile_update.looking_for_gender is not None:
        profile.looking_for_gender = profile_update.looking_for_gender
    if profile_update.min_age is not None:
        profile.min_age = profile_update.min_age
    if profile_update.max_age is not None:
        profile.max_age = profile_update.max_age
    if profile_update.max_distance_km is not None:
        profile.max_distance_km = profile_update.max_distance_km

    # Recalculate completeness score
    profile.completeness_score = calculate_completeness_score(profile)
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)

    # Return updated profile
    location = parse_location(profile.location)
    photos = parse_photos(profile.photos)

    return ProfileResponse(
        user_id=profile.user_id,
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        bio=profile.bio,
        photos=photos,
        location=location,
        completeness_score=profile.completeness_score,
        looking_for_gender=profile.looking_for_gender,
        min_age=profile.min_age,
        max_age=profile.max_age,
        max_distance_km=profile.max_distance_km,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post("/{user_id}/photos", response_model=PhotoUploadResponse)
async def upload_photo(
    user_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoUploadResponse:
    """
    Upload photo to user profile.

    Args:
        user_id: User UUID
        file: Photo file to upload
        db: Database session
        current_user: Authenticated user

    Returns:
        Photo upload response with URL and metadata

    Raises:
        HTTPException: If validation fails or max photos exceeded
    """
    # Check authorization
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload photos")

    profile = db.get(Profile, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Check photo count limit
    photos_list = profile.photos if isinstance(profile.photos, list) else []
    if len(photos_list) >= 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 6 photos allowed")

    # Read file content
    file_content = await file.read()

    # Detect faces
    face_detected, face_confidence = await storage_service.detect_faces(file_content)

    if not face_detected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in photo. Please upload a photo with your face clearly visible.",
        )

    # Upload to S3
    try:
        photo_id, photo_url = await storage_service.upload_photo(
            user_id=str(user_id),
            file_bytes=file_content,
            filename=file.filename or "photo.jpg",
            content_type=file.content_type or "image/jpeg",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

    # Add photo to profile
    photo_data = {
        "photo_id": photo_id,
        "url": photo_url,
        "uploaded_at": datetime.utcnow().isoformat(),
        "order": len(photos_list),
    }
    photos_list.append(photo_data)
    profile.photos = photos_list

    # Recalculate completeness score
    profile.completeness_score = calculate_completeness_score(profile)

    db.commit()

    return PhotoUploadResponse(
        photo_id=photo_id,
        url=photo_url,
        uploaded_at=datetime.utcnow(),
        order=len(photos_list) - 1,
        face_detected=face_detected,
        face_confidence=face_confidence,
    )


@router.delete("/{user_id}/photos/{photo_id}", response_model=PhotoDeleteResponse)
async def delete_photo(
    user_id: UUID,
    photo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoDeleteResponse:
    """
    Delete photo from user profile.

    Args:
        user_id: User UUID
        photo_id: Photo UUID to delete
        db: Database session
        current_user: Authenticated user

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If photo not found or user not authorized
    """
    # Check authorization
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete photos")

    profile = db.get(Profile, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Find photo in profile
    photos_list = profile.photos if isinstance(profile.photos, list) else []
    photo_to_delete = next((p for p in photos_list if p.get("photo_id") == photo_id), None)

    if not photo_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    # Delete from S3
    file_extension = photo_to_delete.get("url", "").rsplit(".", 1)[-1] or "jpg"
    try:
        await storage_service.delete_photo(str(user_id), photo_id, file_extension)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Deletion failed: {str(e)}")

    # Remove from profile
    photos_list = [p for p in photos_list if p.get("photo_id") != photo_id]

    # Reorder remaining photos
    for idx, photo in enumerate(photos_list):
        photo["order"] = idx

    profile.photos = photos_list

    # Recalculate completeness score
    profile.completeness_score = calculate_completeness_score(profile)

    db.commit()

    return PhotoDeleteResponse(message="Photo deleted successfully", deleted_photo_id=photo_id)
