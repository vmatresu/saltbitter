"""GDPR data export functionality - Right to Access (Article 15)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    AIInteraction,
    AttachmentAssessment,
    ComplianceLog,
    ConsentLog,
    Match,
    Message,
    Profile,
    RefreshToken,
    User,
)


async def export_user_data(db: AsyncSession, user_id: UUID) -> dict[str, Any]:
    """
    Export all user data in machine-readable format (GDPR Article 15).

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        Complete user data export as dictionary

    Raises:
        ValueError: If user not found
    """
    # Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Fetch profile
    profile_result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()

    # Fetch attachment assessment
    assessment_result = await db.execute(
        select(AttachmentAssessment).where(AttachmentAssessment.user_id == user_id)
    )
    assessment = assessment_result.scalar_one_or_none()

    # Fetch matches
    matches_result = await db.execute(
        select(Match).where((Match.user_a_id == user_id) | (Match.user_b_id == user_id))
    )
    matches = matches_result.scalars().all()

    # Fetch messages (sent and received)
    messages_result = await db.execute(
        select(Message).where((Message.from_user_id == user_id) | (Message.to_user_id == user_id))
    )
    messages = messages_result.scalars().all()

    # Fetch AI interactions
    ai_interactions_result = await db.execute(
        select(AIInteraction).where(AIInteraction.user_id == user_id)
    )
    ai_interactions = ai_interactions_result.scalars().all()

    # Fetch consent logs
    consent_logs_result = await db.execute(select(ConsentLog).where(ConsentLog.user_id == user_id))
    consent_logs = consent_logs_result.scalars().all()

    # Fetch compliance logs
    compliance_logs_result = await db.execute(
        select(ComplianceLog).where(ComplianceLog.user_id == user_id)
    )
    compliance_logs = compliance_logs_result.scalars().all()

    # Build export data
    export_data: dict[str, Any] = {
        "personal_information": {
            "user_id": str(user.id),
            "email": user.email,
            "verified": user.verified,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        },
        "profile": None,
        "attachment_assessment": None,
        "matches": [],
        "messages": [],
        "ai_interactions": [],
        "consent_history": [],
        "compliance_logs": [],
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "regulatory_framework": "GDPR Article 15",
        },
    }

    # Add profile data
    if profile:
        export_data["profile"] = {
            "name": profile.name,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "gender": profile.gender,
            "bio": profile.bio,
            "location": profile.location,
            "photos": profile.photos,
            "interests": profile.interests,
            "preferences": profile.preferences,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

    # Add attachment assessment (special category data - Article 9)
    if assessment:
        export_data["attachment_assessment"] = {
            "anxiety_score": float(assessment.anxiety_score),
            "avoidance_score": float(assessment.avoidance_score),
            "attachment_style": assessment.attachment_style,
            "responses": assessment.responses,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "note": "This is special category data under GDPR Article 9",
        }

    # Add matches
    for match in matches:
        export_data["matches"].append(
            {
                "match_id": str(match.id),
                "other_user_id": str(
                    match.user_b_id if match.user_a_id == user_id else match.user_a_id
                ),
                "compatibility_score": float(match.compatibility_score)
                if match.compatibility_score
                else None,
                "status": match.status,
                "created_at": match.created_at.isoformat(),
            }
        )

    # Add messages
    for message in messages:
        export_data["messages"].append(
            {
                "message_id": str(message.id),
                "from_user_id": str(message.from_user_id),
                "to_user_id": str(message.to_user_id),
                "content": message.content,
                "sent_at": message.sent_at.isoformat(),
            }
        )

    # Add AI interactions
    for ai_interaction in ai_interactions:
        export_data["ai_interactions"].append(
            {
                "interaction_id": str(ai_interaction.id),
                "ai_type": ai_interaction.ai_type,
                "disclosure_shown": ai_interaction.disclosure_shown,
                "created_at": ai_interaction.created_at.isoformat(),
                "note": "AI interactions logged per EU AI Act Article 52",
            }
        )

    # Add consent history
    for consent in consent_logs:
        export_data["consent_history"].append(
            {
                "consent_id": str(consent.id),
                "consent_type": consent.consent_type,
                "granted": consent.granted,
                "timestamp": consent.timestamp.isoformat(),
            }
        )

    # Add compliance logs
    for log in compliance_logs:
        export_data["compliance_logs"].append(
            {
                "log_id": str(log.id),
                "action_type": log.action_type,
                "action_metadata": log.action_metadata,
                "regulatory_framework": log.regulatory_framework,
                "timestamp": log.timestamp.isoformat(),
            }
        )

    return export_data
