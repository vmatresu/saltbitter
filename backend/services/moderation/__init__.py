"""Content moderation service with Perspective API and AWS Rekognition."""

from .routes import router as moderation_router

__all__ = ["moderation_router"]
