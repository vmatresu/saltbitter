"""
Pydantic schemas for profile endpoints.

Defines request/response models for profile management, photo uploads,
and profile completeness calculations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LocationInput(BaseModel):
    """Location coordinates input schema."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's display name")
    age: Optional[int] = Field(None, ge=18, le=100, description="User's age (18-100)")
    gender: Optional[str] = Field(None, description="Gender (male/female/non-binary/other)")
    bio: Optional[str] = Field(None, max_length=500, description="User bio (max 500 chars)")
    location: Optional[LocationInput] = Field(None, description="User location coordinates")

    # Preferences
    looking_for_gender: Optional[str] = Field(None, description="Preferred gender to match with")
    min_age: Optional[int] = Field(None, ge=18, le=100, description="Minimum age preference")
    max_age: Optional[int] = Field(None, ge=18, le=100, description="Maximum age preference")
    max_distance_km: Optional[int] = Field(None, ge=1, le=500, description="Maximum distance (1-500 km)")

    @field_validator("gender", "looking_for_gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender values."""
        if v is None:
            return v
        valid_genders = {"male", "female", "non-binary", "other"}
        if v.lower() not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v.lower()

    @field_validator("max_age")
    @classmethod
    def validate_age_range(cls, v: Optional[int], info: Any) -> Optional[int]:
        """Validate max_age is greater than min_age."""
        if v is not None and "min_age" in info.data and info.data["min_age"] is not None:
            if v < info.data["min_age"]:
                raise ValueError("max_age must be greater than or equal to min_age")
        return v


class PhotoInfo(BaseModel):
    """Photo information schema."""

    photo_id: str = Field(..., description="Unique photo identifier")
    url: str = Field(..., description="CDN URL for photo")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    order: int = Field(..., description="Display order (0-5)")


class ProfileResponse(BaseModel):
    """Response schema for user profile."""

    user_id: UUID = Field(..., description="User UUID")
    name: str = Field(..., description="User's display name")
    age: int = Field(..., description="User's age")
    gender: str = Field(..., description="User's gender")
    bio: Optional[str] = Field(None, description="User bio")
    photos: list[PhotoInfo] = Field(default_factory=list, description="User photos (max 6)")
    location: Optional[dict[str, float]] = Field(None, description="Location coordinates {lat, lng}")
    completeness_score: float = Field(..., description="Profile completeness (0-100%)")

    # Preferences
    looking_for_gender: Optional[str] = Field(None, description="Preferred gender to match with")
    min_age: Optional[int] = Field(None, description="Minimum age preference")
    max_age: Optional[int] = Field(None, description="Maximum age preference")
    max_distance_km: Optional[int] = Field(None, description="Maximum distance preference")

    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PhotoUploadResponse(BaseModel):
    """Response schema for photo upload."""

    photo_id: str = Field(..., description="Unique photo identifier")
    url: str = Field(..., description="CDN URL for uploaded photo")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    order: int = Field(..., description="Display order")
    message: str = Field(default="Photo uploaded successfully", description="Success message")
    face_detected: bool = Field(..., description="Whether face was detected")
    face_confidence: Optional[float] = Field(None, description="Face detection confidence (0-100)")


class PhotoDeleteResponse(BaseModel):
    """Response schema for photo deletion."""

    message: str = Field(..., description="Deletion confirmation message")
    deleted_photo_id: str = Field(..., description="ID of deleted photo")


class ProfileCompletenessResponse(BaseModel):
    """Response schema for profile completeness calculation."""

    completeness_score: float = Field(..., description="Profile completeness (0-100%)")
    missing_fields: list[str] = Field(..., description="List of missing optional fields")
    completed_fields: list[str] = Field(..., description="List of completed fields")
