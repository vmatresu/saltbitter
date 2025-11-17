"""Tests for GDPR compliance functionality."""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Profile, AttachmentAssessment
from services.compliance.gdpr import GDPRService, log_compliance_action
from services.compliance.data_export import export_user_data
from services.compliance.data_deletion import (
    schedule_account_deletion,
    execute_account_deletion,
    anonymize_user_data,
)
from services.compliance.consent import (
    grant_consent,
    withdraw_consent,
    get_consent_status,
    check_consent_granted,
)


@pytest.mark.asyncio
async def test_export_user_data(db_session: AsyncSession):
    """Test GDPR data export (Article 15)."""
    # Create test user
    user = User(
        email="test@example.com",
        password_hash="hashed",
        verified=True,
        subscription_tier="premium",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create profile
    profile = Profile(
        user_id=user.id,
        name="Test User",
        bio="Test bio",
        gender="male",
        location="San Francisco, CA",
    )
    db_session.add(profile)
    await db_session.commit()

    # Export data
    export = await export_user_data(db_session, user.id)

    # Verify export structure
    assert export["personal_information"]["email"] == "test@example.com"
    assert export["personal_information"]["subscription_tier"] == "premium"
    assert export["profile"]["name"] == "Test User"
    assert export["export_metadata"]["format_version"] == "1.0"
    assert "exported_at" in export["export_metadata"]


@pytest.mark.asyncio
async def test_export_nonexistent_user(db_session: AsyncSession):
    """Test data export for nonexistent user raises error."""
    with pytest.raises(ValueError, match="User .* not found"):
        await export_user_data(db_session, uuid4())


@pytest.mark.asyncio
async def test_schedule_account_deletion(db_session: AsyncSession):
    """Test account deletion scheduling (Article 17)."""
    # Create test user
    user = User(
        email="delete@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Schedule deletion
    deletion_date = await schedule_account_deletion(db_session, user.id, grace_period_days=30)

    # Verify deletion date is ~30 days in future
    assert deletion_date > datetime.utcnow()
    # Allow 1 minute tolerance for test execution time
    assert (deletion_date - datetime.utcnow()).days >= 29


@pytest.mark.asyncio
async def test_execute_account_deletion(db_session: AsyncSession):
    """Test permanent account deletion."""
    # Create test user
    user = User(
        email="todelete@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user_id = user.id

    # Execute deletion
    success = await execute_account_deletion(db_session, user_id)

    assert success

    # Verify user is deleted
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.id == user_id))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None


@pytest.mark.asyncio
async def test_grant_consent(db_session: AsyncSession):
    """Test granting consent for data processing."""
    # Create test user
    user = User(
        email="consent@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Grant consent
    consent = await grant_consent(
        db_session,
        user.id,
        "psychological_assessment",
        consent_text="I consent to psychological assessment",
        ip_address="192.168.1.1",
    )

    assert consent.user_id == user.id
    assert consent.consent_type == "psychological_assessment"
    assert consent.granted is True
    assert consent.ip_address == "192.168.1.1"


@pytest.mark.asyncio
async def test_withdraw_consent(db_session: AsyncSession):
    """Test withdrawing consent."""
    # Create test user
    user = User(
        email="withdraw@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Grant then withdraw consent
    await grant_consent(db_session, user.id, "ai_features")
    withdrawal = await withdraw_consent(db_session, user.id, "ai_features")

    assert withdrawal.granted is False


@pytest.mark.asyncio
async def test_get_consent_status(db_session: AsyncSession):
    """Test getting consent status for all types."""
    # Create test user
    user = User(
        email="status@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Grant multiple consents
    await grant_consent(db_session, user.id, "profile_data")
    await grant_consent(db_session, user.id, "psychological_assessment")
    await grant_consent(db_session, user.id, "ai_features")
    await withdraw_consent(db_session, user.id, "marketing")

    # Get status
    status = await get_consent_status(db_session, user.id)

    assert status["profile_data"] is True
    assert status["psychological_assessment"] is True
    assert status["ai_features"] is True
    assert status["marketing"] is False


@pytest.mark.asyncio
async def test_check_consent_granted(db_session: AsyncSession):
    """Test checking if specific consent is granted."""
    # Create test user
    user = User(
        email="check@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Grant consent
    await grant_consent(db_session, user.id, "psychological_assessment")

    # Check consent
    has_consent = await check_consent_granted(
        db_session, user.id, "psychological_assessment"
    )
    assert has_consent is True

    no_consent = await check_consent_granted(
        db_session, user.id, "nonexistent_type"
    )
    assert no_consent is False


@pytest.mark.asyncio
async def test_anonymize_user_data(db_session: AsyncSession):
    """Test data anonymization alternative to deletion."""
    # Create test user
    user = User(
        email="anonymize@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user_id = user.id

    # Anonymize
    success = await anonymize_user_data(db_session, user_id)
    assert success

    # Verify user is anonymized
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.id == user_id))
    anon_user = result.scalar_one_or_none()
    assert anon_user is not None
    assert anon_user.email == f"deleted-{user_id}@deleted.local"
    assert anon_user.password_hash == "DELETED"


@pytest.mark.asyncio
async def test_log_compliance_action(db_session: AsyncSession):
    """Test logging compliance actions for audit trail."""
    # Create test user
    user = User(
        email="log@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Log action
    log = await log_compliance_action(
        db_session,
        user.id,
        "data_export",
        {"exported_at": datetime.utcnow().isoformat()},
        "gdpr",
    )

    assert log.user_id == user.id
    assert log.action_type == "data_export"
    assert log.regulatory_framework == "gdpr"


@pytest.mark.asyncio
async def test_gdpr_service_integration(db_session: AsyncSession):
    """Test GDPRService integration."""
    # Create test user
    user = User(
        email="service@example.com",
        password_hash="hashed",
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Initialize service
    gdpr_service = GDPRService(db_session)

    # Test export
    data = await gdpr_service.export_user_data(user.id)
    assert data["personal_information"]["email"] == "service@example.com"

    # Test consent
    consent = await gdpr_service.grant_consent(user.id, "ai_features")
    assert consent["granted"] is True

    # Test consent status
    status = await gdpr_service.get_consent_status(user.id)
    assert status["ai_features"] is True

    # Test DPO contact
    dpo = gdpr_service.get_dpo_contact()
    assert dpo["email"] == "dpo@saltbitter.com"
