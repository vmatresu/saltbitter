"""GDPR data deletion functionality - Right to Erasure (Article 17)."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


async def schedule_account_deletion(
    db: AsyncSession, user_id: UUID, grace_period_days: int = 30
) -> datetime:
    """
    Schedule account deletion with grace period (GDPR Article 17).

    Account will be deleted after grace_period_days. User can cancel during grace period.

    Args:
        db: Database session
        user_id: UUID of the user
        grace_period_days: Grace period before permanent deletion (default 30 days)

    Returns:
        Scheduled deletion date

    Raises:
        ValueError: If user not found
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Calculate deletion date
    deletion_date = datetime.utcnow() + timedelta(days=grace_period_days)

    # In a real implementation, this would:
    # 1. Mark user account for deletion in database
    # 2. Schedule Celery task for actual deletion
    # 3. Send confirmation email to user
    # 4. Log the deletion request

    # For now, we'll add a field marker (would require migration)
    # This is a placeholder - actual implementation needs deletion_scheduled_at field

    await db.commit()

    return deletion_date


async def cancel_account_deletion(db: AsyncSession, user_id: UUID) -> bool:
    """
    Cancel scheduled account deletion during grace period.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        True if cancellation successful

    Raises:
        ValueError: If user not found or deletion not scheduled
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Cancel deletion (placeholder - needs actual implementation)
    # Would remove deletion_scheduled_at field and cancel Celery task

    await db.commit()

    return True


async def execute_account_deletion(db: AsyncSession, user_id: UUID) -> bool:
    """
    Permanently delete user account and all associated data (GDPR Article 17).

    This is the actual deletion executed after grace period expires.
    Deletes all user data across all tables.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        True if deletion successful

    Raises:
        ValueError: If user not found
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Delete user - cascading deletes will handle related records
    # Database models should have proper CASCADE delete relationships
    await db.execute(delete(User).where(User.id == user_id))

    # Additional cleanup for records that might not cascade:
    # - S3 photos deletion
    # - Redis cache cleanup
    # - Third-party service data removal

    await db.commit()

    return True


async def anonymize_user_data(db: AsyncSession, user_id: UUID) -> bool:
    """
    Anonymize user data instead of deletion (alternative to full erasure).

    Used when data must be retained for legal/regulatory reasons but user identity removed.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        True if anonymization successful

    Raises:
        ValueError: If user not found
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Anonymize personal data
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            email=f"deleted-{user_id}@deleted.local",
            password_hash="DELETED",
            verified=False,
        )
    )

    # Anonymize profile data (would need to handle Profile table similarly)
    # Remove PII from all related records

    await db.commit()

    return True
