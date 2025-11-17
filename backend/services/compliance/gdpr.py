"""Main GDPR compliance module coordinating all GDPR functionality."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.compliance import ComplianceLog

from .consent import check_consent_granted, get_consent_status, grant_consent, withdraw_consent
from .data_deletion import execute_account_deletion, schedule_account_deletion
from .data_export import export_user_data
from .dpo import DataProtectionOfficer


async def log_compliance_action(
    db: AsyncSession,
    user_id: UUID,
    action_type: str,
    action_metadata: dict,
    regulatory_framework: str = "gdpr",
) -> ComplianceLog:
    """
    Log compliance action for audit trail.

    Args:
        db: Database session
        user_id: UUID of the user
        action_type: Type of action (data_export, data_deletion, consent, etc.)
        action_metadata: Additional metadata about the action
        regulatory_framework: Regulatory framework (gdpr, eu_ai_act, ccpa, etc.)

    Returns:
        ComplianceLog record
    """
    log = ComplianceLog(
        user_id=user_id,
        action_type=action_type,
        action_metadata=action_metadata,
        regulatory_framework=regulatory_framework,
        timestamp=datetime.utcnow(),
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log


class GDPRService:
    """
    GDPR compliance service coordinating all GDPR functionality.

    Provides unified interface for GDPR operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize GDPR service with database session."""
        self.db = db

    async def export_user_data(self, user_id: UUID) -> dict:
        """
        Export all user data (Right to Access - Article 15).

        Args:
            user_id: UUID of the user

        Returns:
            Complete user data export
        """
        data = await export_user_data(self.db, user_id)

        # Log the export
        await log_compliance_action(
            self.db,
            user_id,
            "data_export",
            {
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0",
                "article": "GDPR Article 15",
            },
        )

        return data

    async def schedule_deletion(self, user_id: UUID, grace_period_days: int = 30) -> datetime:
        """
        Schedule account deletion (Right to Erasure - Article 17).

        Args:
            user_id: UUID of the user
            grace_period_days: Grace period before deletion

        Returns:
            Scheduled deletion date
        """
        deletion_date = await schedule_account_deletion(
            self.db, user_id, grace_period_days
        )

        # Log the deletion request
        await log_compliance_action(
            self.db,
            user_id,
            "data_deletion_scheduled",
            {
                "scheduled_for": deletion_date.isoformat(),
                "grace_period_days": grace_period_days,
                "article": "GDPR Article 17",
            },
        )

        return deletion_date

    async def grant_consent(
        self,
        user_id: UUID,
        consent_type: str,
        consent_text: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        """
        Grant user consent for data processing.

        Args:
            user_id: UUID of the user
            consent_type: Type of consent
            consent_text: Text of consent shown to user
            ip_address: IP address for audit trail

        Returns:
            Consent record
        """
        consent = await grant_consent(
            self.db, user_id, consent_type, consent_text, ip_address
        )

        return {
            "id": str(consent.id),
            "user_id": str(consent.user_id),
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "timestamp": consent.timestamp.isoformat(),
        }

    async def withdraw_consent(
        self, user_id: UUID, consent_type: str, ip_address: str | None = None
    ) -> dict:
        """
        Withdraw user consent.

        Args:
            user_id: UUID of the user
            consent_type: Type of consent to withdraw
            ip_address: IP address for audit trail

        Returns:
            Consent record
        """
        consent = await withdraw_consent(self.db, user_id, consent_type, ip_address)

        return {
            "id": str(consent.id),
            "user_id": str(consent.user_id),
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "timestamp": consent.timestamp.isoformat(),
        }

    async def get_consent_status(self, user_id: UUID) -> dict[str, bool]:
        """
        Get current consent status for user.

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary mapping consent type to granted status
        """
        return await get_consent_status(self.db, user_id)

    async def check_consent(self, user_id: UUID, consent_type: str) -> bool:
        """
        Check if user has granted specific consent.

        Args:
            user_id: UUID of the user
            consent_type: Type of consent to check

        Returns:
            True if consent granted, False otherwise
        """
        return await check_consent_granted(self.db, user_id, consent_type)

    @staticmethod
    def get_dpo_contact() -> dict:
        """Get Data Protection Officer contact information."""
        return DataProtectionOfficer.get_contact_info()
