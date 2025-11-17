"""FastAPI routes for GDPR compliance endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.auth.security import get_current_user, get_db

from .gdpr import GDPRService
from .schemas import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    ConsentRequest,
    ConsentResponse,
    ConsentStatusResponse,
    DataExportResponse,
    DPOContactResponse,
    PrivacyPolicyResponse,
)

router = APIRouter(prefix="/api/gdpr", tags=["GDPR Compliance"])


@router.get("/export", response_model=DataExportResponse)
async def export_user_data(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataExportResponse:
    """
    Export complete user data (GDPR Article 15 - Right to Access).

    Returns all personal data in machine-readable JSON format.
    """
    try:
        gdpr_service = GDPRService(db)
        user_data = await gdpr_service.export_user_data(current_user.id)

        return DataExportResponse(
            user_data=user_data,
            exported_at=datetime.utcnow(),
            format_version="1.0",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user data: {str(e)}",
        )


@router.post("/delete-account", response_model=AccountDeletionResponse)
async def delete_account(
    request: AccountDeletionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountDeletionResponse:
    """
    Schedule account deletion (GDPR Article 17 - Right to Erasure).

    Account will be deleted after 30-day grace period.
    User can cancel deletion during grace period.
    """
    # Verify email confirmation
    if request.confirmation_email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation email does not match account email",
        )

    try:
        gdpr_service = GDPRService(db)
        scheduled_date = await gdpr_service.schedule_deletion(current_user.id)

        return AccountDeletionResponse(
            deletion_scheduled=True,
            scheduled_date=scheduled_date,
            grace_period_days=30,
            message="Account deletion scheduled. You can cancel within 30 days by logging in.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule account deletion: {str(e)}",
        )


@router.get("/consent-status", response_model=ConsentStatusResponse)
async def get_consent_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentStatusResponse:
    """
    Get current consent status for all consent types.

    Returns map of consent type to granted status.
    """
    try:
        gdpr_service = GDPRService(db)
        consents = await gdpr_service.get_consent_status(current_user.id)

        return ConsentStatusResponse(consents=consents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}",
        )


@router.post("/consent", response_model=ConsentResponse)
async def manage_consent(
    consent_request: ConsentRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentResponse:
    """
    Grant or withdraw consent for data processing.

    Required for special category data (GDPR Article 9).
    """
    try:
        gdpr_service = GDPRService(db)
        ip_address = request.client.host if request.client else None

        if consent_request.granted:
            consent = await gdpr_service.grant_consent(
                current_user.id,
                consent_request.consent_type,
                consent_request.consent_text,
                ip_address,
            )
        else:
            consent = await gdpr_service.withdraw_consent(
                current_user.id,
                consent_request.consent_type,
                ip_address,
            )

        return ConsentResponse(
            id=consent["id"],
            user_id=consent["user_id"],
            consent_type=consent["consent_type"],
            granted=consent["granted"],
            timestamp=datetime.fromisoformat(consent["timestamp"]),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage consent: {str(e)}",
        )


@router.get("/dpo-contact", response_model=DPOContactResponse)
async def get_dpo_contact() -> DPOContactResponse:
    """
    Get Data Protection Officer contact information.

    Required under GDPR Article 37.
    """
    dpo_info = GDPRService.get_dpo_contact()

    return DPOContactResponse(
        name=dpo_info["name"],
        email=dpo_info["email"],
        phone=dpo_info.get("phone"),
        address=dpo_info.get("address"),
    )


# Legal document routes
@router.get("/privacy-policy", response_model=PrivacyPolicyResponse)
async def get_privacy_policy() -> PrivacyPolicyResponse:
    """
    Get privacy policy.

    Returns current version of privacy policy.
    """
    # In real implementation, read from file or database
    return PrivacyPolicyResponse(
        content="Privacy policy content would be loaded from file",
        version="1.0.0",
        effective_date=datetime(2025, 1, 1),
        last_updated=datetime(2025, 1, 1),
    )


@router.get("/terms-of-service", response_model=PrivacyPolicyResponse)
async def get_terms_of_service() -> PrivacyPolicyResponse:
    """
    Get terms of service.

    Returns current version of terms of service.
    """
    # In real implementation, read from file or database
    return PrivacyPolicyResponse(
        content="Terms of service content would be loaded from file",
        version="1.0.0",
        effective_date=datetime(2025, 1, 1),
        last_updated=datetime(2025, 1, 1),
    )
