"""User reporting system."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.moderation import (
    ModerationAction,
    ModerationAuditLog,
    ModerationStatus,
    ReportReason,
    UserReport,
)


async def create_report(
    db: AsyncSession,
    reporter_id: UUID,
    reported_user_id: UUID,
    content_type: str,
    reason: ReportReason,
    description: str,
    content_id: UUID | None = None,
) -> UserReport:
    """
    Create a user report.

    Args:
        db: Database session
        reporter_id: ID of user creating the report
        reported_user_id: ID of user being reported
        content_type: Type of content (message, profile, behavior)
        reason: Reason for report
        description: Description of the issue
        content_id: Optional ID of specific content being reported

    Returns:
        Created UserReport instance

    Raises:
        ValueError: If trying to report oneself
    """
    if reporter_id == reported_user_id:
        raise ValueError("Cannot report yourself")

    # Create report
    report = UserReport(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        content_type=content_type,
        content_id=content_id,
        reason=reason,
        description=description,
        status=ModerationStatus.PENDING,
    )
    db.add(report)

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=ModerationAction.MANUAL_REVIEW,
        content_type=content_type,
        content_id=content_id or reported_user_id,
        user_id=reported_user_id,
        moderator_id=reporter_id,
        reason=f"User report: {reason.value}",
        metadata={
            "reporter_id": str(reporter_id),
            "reported_user_id": str(reported_user_id),
            "reason": reason.value,
            "description": description,
        },
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(report)

    return report


async def get_report(db: AsyncSession, report_id: UUID) -> UserReport | None:
    """
    Get a report by ID.

    Args:
        db: Database session
        report_id: Report ID

    Returns:
        UserReport instance or None if not found
    """
    result = await db.execute(select(UserReport).where(UserReport.id == report_id))
    return result.scalar_one_or_none()


async def get_pending_reports(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[UserReport]:
    """
    Get pending reports for review.

    Args:
        db: Database session
        limit: Maximum number of reports to return
        offset: Offset for pagination

    Returns:
        List of pending UserReport instances
    """
    result = await db.execute(
        select(UserReport)
        .where(UserReport.status == ModerationStatus.PENDING)
        .order_by(UserReport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_reports_by_user(
    db: AsyncSession, reported_user_id: UUID, limit: int = 20
) -> list[UserReport]:
    """
    Get all reports for a specific user.

    Args:
        db: Database session
        reported_user_id: ID of reported user
        limit: Maximum number of reports to return

    Returns:
        List of UserReport instances
    """
    result = await db.execute(
        select(UserReport)
        .where(UserReport.reported_user_id == reported_user_id)
        .order_by(UserReport.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_report_status(
    db: AsyncSession,
    report_id: UUID,
    moderator_id: UUID,
    action: ModerationAction,
    notes: str | None = None,
) -> UserReport:
    """
    Update a report's status after review.

    Args:
        db: Database session
        report_id: Report ID
        moderator_id: ID of moderator reviewing the report
        action: Action taken
        notes: Optional moderator notes

    Returns:
        Updated UserReport instance

    Raises:
        ValueError: If report not found
    """
    report = await get_report(db, report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")

    # Update report
    report.status = (
        ModerationStatus.APPROVED if action == ModerationAction.APPROVED else ModerationStatus.REJECTED
    )
    report.reviewed_by = moderator_id
    report.action_taken = action
    report.moderator_notes = notes

    # Create audit log entry
    audit_log = ModerationAuditLog(
        action_type=action,
        content_type=report.content_type,
        content_id=report.content_id or report.reported_user_id,
        user_id=report.reported_user_id,
        moderator_id=moderator_id,
        reason=notes,
        metadata={
            "report_id": str(report_id),
            "original_reason": report.reason.value,
        },
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(report)

    return report
