"""Data Protection Officer (DPO) contact information and responsibilities."""

from datetime import datetime


class DataProtectionOfficer:
    """
    Data Protection Officer information and contact details.

    Required under GDPR Article 37 for organizations processing special category data.
    """

    NAME = "SaltBitter Data Protection Officer"
    EMAIL = "dpo@saltbitter.com"
    PHONE = "+1-555-PRIVACY"
    ADDRESS = """
    SaltBitter, Inc.
    Data Protection Officer
    123 Privacy Street
    San Francisco, CA 94102
    United States
    """

    @staticmethod
    def get_contact_info() -> dict[str, str | None]:
        """
        Get DPO contact information.

        Returns:
            Dictionary with DPO contact details
        """
        return {
            "name": DataProtectionOfficer.NAME,
            "email": DataProtectionOfficer.EMAIL,
            "phone": DataProtectionOfficer.PHONE,
            "address": DataProtectionOfficer.ADDRESS.strip(),
        }

    @staticmethod
    def get_responsibilities() -> list[str]:
        """
        Get list of DPO responsibilities under GDPR.

        Returns:
            List of DPO responsibilities
        """
        return [
            "Monitor compliance with GDPR and other data protection laws",
            "Advise on data protection impact assessments (DPIAs)",
            "Cooperate with supervisory authorities",
            "Act as contact point for supervisory authorities and data subjects",
            "Inform and advise on data protection obligations",
            "Monitor assignment of responsibilities and training",
            "Handle data breach notifications and investigations",
            "Maintain records of processing activities",
            "Oversee consent management and data subject rights requests",
        ]

    @staticmethod
    def log_dpo_contact(
        user_id: str, contact_reason: str, contact_method: str = "email"
    ) -> dict[str, any]:
        """
        Log contact with DPO for audit trail.

        Args:
            user_id: ID of the user contacting DPO
            contact_reason: Reason for contact
            contact_method: Method of contact (email, phone, etc.)

        Returns:
            Contact log record
        """
        return {
            "user_id": user_id,
            "contact_reason": contact_reason,
            "contact_method": contact_method,
            "contacted_at": datetime.utcnow().isoformat(),
            "dpo_email": DataProtectionOfficer.EMAIL,
        }
