"""GDPR consent management - Article 9 (special category data)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.compliance import ConsentLog


async def grant_consent(
    db: AsyncSession,
    user_id: UUID,
    consent_type: str,
    consent_text: str | None = None,
    ip_address: str | None = None,
) -> ConsentLog:
    """
    Record user consent for data processing.

    Args:
        db: Database session
        user_id: UUID of the user
        consent_type: Type of consent (e.g., psychological_assessment, ai_features)
        consent_text: Text of consent shown to user
        ip_address: IP address for audit trail

    Returns:
        ConsentLog record
    """
    consent = ConsentLog(
        user_id=user_id,
        consent_type=consent_type,
        granted=True,
        consent_text=consent_text,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )

    db.add(consent)
    await db.commit()
    await db.refresh(consent)

    return consent


async def withdraw_consent(
    db: AsyncSession,
    user_id: UUID,
    consent_type: str,
    ip_address: str | None = None,
) -> ConsentLog:
    """
    Record user consent withdrawal.

    Args:
        db: Database session
        user_id: UUID of the user
        consent_type: Type of consent being withdrawn
        ip_address: IP address for audit trail

    Returns:
        ConsentLog record
    """
    consent = ConsentLog(
        user_id=user_id,
        consent_type=consent_type,
        granted=False,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )

    db.add(consent)
    await db.commit()
    await db.refresh(consent)

    return consent


async def get_consent_status(db: AsyncSession, user_id: UUID) -> dict[str, bool]:
    """
    Get current consent status for all consent types for a user.

    Returns the most recent consent decision for each consent type.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        Dictionary mapping consent type to granted status
    """
    # Fetch all consent logs for user, ordered by timestamp descending
    result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.user_id == user_id)
        .order_by(ConsentLog.timestamp.desc())
    )
    consents = result.scalars().all()

    # Build consent status map (most recent per type)
    consent_status: dict[str, bool] = {}
    for consent in consents:
        if consent.consent_type not in consent_status:
            consent_status[consent.consent_type] = consent.granted

    return consent_status


async def check_consent_granted(
    db: AsyncSession, user_id: UUID, consent_type: str
) -> bool:
    """
    Check if user has granted specific consent type.

    Args:
        db: Database session
        user_id: UUID of the user
        consent_type: Type of consent to check

    Returns:
        True if consent granted, False otherwise
    """
    # Get most recent consent for this type
    result = await db.execute(
        select(ConsentLog)
        .where(
            ConsentLog.user_id == user_id,
            ConsentLog.consent_type == consent_type,
        )
        .order_by(ConsentLog.timestamp.desc())
        .limit(1)
    )
    consent = result.scalar_one_or_none()

    return consent.granted if consent else False


async def require_consent_for_psychological_data(
    db: AsyncSession, user_id: UUID
) -> bool:
    """
    Check if user has granted consent for psychological assessment (GDPR Article 9).

    Psychological data is special category data requiring explicit consent.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        True if consent granted, False otherwise

    Raises:
        PermissionError: If consent not granted
    """
    has_consent = await check_consent_granted(
        db, user_id, "psychological_assessment"
    )

    if not has_consent:
        raise PermissionError(
            "Explicit consent required for psychological assessment "
            "(GDPR Article 9 - special category data)"
        )

    return True
