"""
Profile service module.

Provides profile management functionality including profile CRUD operations,
photo uploads with face detection, and profile completeness calculations.
"""

from .routes import router as profile_router
from .schemas import (
    PhotoDeleteResponse,
    PhotoInfo,
    PhotoUploadResponse,
    ProfileCompletenessResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from .storage import storage_service

__all__ = [
    "profile_router",
    "ProfileResponse",
    "ProfileUpdateRequest",
    "PhotoUploadResponse",
    "PhotoDeleteResponse",
    "PhotoInfo",
    "ProfileCompletenessResponse",
    "storage_service",
]
