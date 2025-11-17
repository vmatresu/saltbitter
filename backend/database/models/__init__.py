"""
SQLAlchemy models for SaltBitter Dating Platform.

All database models are defined here using SQLAlchemy 2.0 ORM.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from geoalchemy2 import Geography
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Import all models to ensure they are registered with Base metadata
from .user import User  # noqa: E402, F401
from .profile import Profile  # noqa: E402, F401
from .attachment import AttachmentAssessment  # noqa: E402, F401
from .match import Match  # noqa: E402, F401
from .message import Message  # noqa: E402, F401
from .ai_interaction import AIInteraction  # noqa: E402, F401
from .subscription import Subscription, Payment  # noqa: E402, F401
from .event import Event, EventRegistration  # noqa: E402, F401
from .compliance import ConsentLog, ComplianceLog  # noqa: E402, F401


__all__ = [
    "Base",
    "User",
    "Profile",
    "AttachmentAssessment",
    "Match",
    "Message",
    "AIInteraction",
    "Subscription",
    "Payment",
    "Event",
    "EventRegistration",
    "ConsentLog",
    "ComplianceLog",
]
