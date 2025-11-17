"""
GDPR Compliance Service for SaltBitter Dating Platform.

This service handles all GDPR compliance requirements including data export,
deletion, consent management, and breach notification.
"""

from fastapi import APIRouter

from .routes import router as compliance_router

__all__ = ["compliance_router"]
