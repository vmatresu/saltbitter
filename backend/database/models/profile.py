"""Profile model for user profile data."""

from datetime import datetime
from uuid import UUID as UUID_TYPE

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Profile(Base):
    """
    User profile model.

    Stores detailed user profile information including bio, photos, location, and preferences.
    """

    __tablename__ = "profiles"

    # Foreign key to users table
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # Basic profile info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(50), nullable=False)  # male, female, non-binary, other
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Photos stored as JSON array of URLs
    photos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.jsonb_build_array()
    )

    # Location using PostGIS geography type (POINT with SRID 4326 for WGS84)
    # Stored as GEOGRAPHY(POINT, 4326) for efficient geospatial queries
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True, index=True
    )

    # Profile completeness score (0-100%)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Preferences
    looking_for_gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_distance_km: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation of Profile."""
        return f"<Profile(user_id={self.user_id}, name={self.name}, age={self.age})>"
