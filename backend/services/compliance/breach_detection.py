"""Data breach detection and notification system (GDPR Article 33 & 34)."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.compliance import ComplianceLog


class BreachSeverity:
    """Breach severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


async def report_data_breach(
    db: AsyncSession,
    severity: str,
    affected_user_ids: list[UUID],
    data_categories: list[str],
    description: str,
    mitigation_steps: str,
) -> UUID:
    """
    Report a data breach and trigger notification process (GDPR Article 33).

    Must notify supervisory authority within 72 hours of becoming aware of breach.

    Args:
        db: Database session
        severity: Breach severity (low, medium, high, critical)
        affected_user_ids: List of affected user IDs
        data_categories: Categories of data compromised
        description: Description of the breach
        mitigation_steps: Steps taken to mitigate

    Returns:
        Breach ID (UUID)
    """
    breach_id = uuid4()
    detected_at = datetime.utcnow()

    # Log breach for each affected user
    for user_id in affected_user_ids:
        breach_log = ComplianceLog(
            user_id=user_id,
            action_type="data_breach",
            action_metadata={
                "breach_id": str(breach_id),
                "severity": severity,
                "detected_at": detected_at.isoformat(),
                "data_categories": data_categories,
                "description": description,
                "mitigation_steps": mitigation_steps,
                "affected_users_count": len(affected_user_ids),
            },
            regulatory_framework="gdpr_article_33",
        )
        db.add(breach_log)

    await db.commit()

    # Trigger notifications
    await notify_dpo_of_breach(
        breach_id, severity, len(affected_user_ids), data_categories, description
    )

    if severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
        await notify_supervisory_authority(
            breach_id, detected_at, affected_user_ids, data_categories, description
        )

    if severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
        # High risk to user rights and freedoms - notify affected users (Article 34)
        await notify_affected_users(
            affected_user_ids, breach_id, description, mitigation_steps
        )

    return breach_id


async def notify_dpo_of_breach(
    breach_id: UUID,
    severity: str,
    affected_count: int,
    data_categories: list[str],
    description: str,
) -> None:
    """
    Notify Data Protection Officer of breach.

    Args:
        breach_id: UUID of the breach
        severity: Breach severity
        affected_count: Number of affected users
        data_categories: Categories of data compromised
        description: Description of the breach
    """
    # In real implementation:
    # - Send email to dpo@saltbitter.com
    # - Create incident in incident management system
    # - Trigger on-call alerts for critical breaches

    print(f"[DPO ALERT] Data breach {breach_id} detected")
    print(f"  Severity: {severity}")
    print(f"  Affected users: {affected_count}")
    print(f"  Data categories: {', '.join(data_categories)}")
    print(f"  Description: {description}")


async def notify_supervisory_authority(
    breach_id: UUID,
    detected_at: datetime,
    affected_user_ids: list[UUID],
    data_categories: list[str],
    description: str,
) -> None:
    """
    Notify supervisory authority within 72 hours (GDPR Article 33).

    Args:
        breach_id: UUID of the breach
        detected_at: When breach was detected
        affected_user_ids: List of affected user IDs
        data_categories: Categories of data compromised
        description: Description of the breach
    """
    # Calculate time remaining for notification
    notification_deadline = detected_at + timedelta(hours=72)
    hours_remaining = (notification_deadline - datetime.utcnow()).total_seconds() / 3600

    print(f"[SUPERVISORY AUTHORITY] Breach notification required")
    print(f"  Breach ID: {breach_id}")
    print(f"  Deadline: {notification_deadline.isoformat()} ({hours_remaining:.1f}h remaining)")
    print(f"  Affected users: {len(affected_user_ids)}")
    print(f"  Data categories: {', '.join(data_categories)}")

    # In real implementation:
    # - Submit notification to relevant supervisory authority
    # - Follow jurisdiction-specific procedures
    # - Document notification in compliance logs


async def notify_affected_users(
    user_ids: list[UUID],
    breach_id: UUID,
    description: str,
    mitigation_steps: str,
) -> None:
    """
    Notify affected users of breach (GDPR Article 34).

    Required when breach likely results in high risk to rights and freedoms.

    Args:
        user_ids: List of affected user IDs
        breach_id: UUID of the breach
        description: Description of the breach
        mitigation_steps: Steps users should take
    """
    print(f"[USER NOTIFICATION] Notifying {len(user_ids)} users of breach {breach_id}")

    # In real implementation:
    # - Send email to each affected user
    # - Provide clear description of breach
    # - Explain potential consequences
    # - Recommend measures to protect themselves
    # - Provide DPO contact information


async def check_breach_notification_deadline(
    db: AsyncSession, breach_id: UUID
) -> dict[str, any]:
    """
    Check if breach notification deadline has been met (72 hours).

    Args:
        db: Database session
        breach_id: UUID of the breach

    Returns:
        Dictionary with deadline status
    """
    # In real implementation:
    # - Query compliance logs for breach
    # - Check if supervisory authority was notified
    # - Calculate time elapsed since detection
    # - Return status and any violations

    return {
        "breach_id": str(breach_id),
        "deadline_met": True,
        "hours_elapsed": 0,
        "notification_sent": False,
    }
