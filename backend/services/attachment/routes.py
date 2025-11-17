"""
Attachment assessment routes.

API endpoints for attachment theory assessment questionnaire, scoring, and results.
"""

import os
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import AttachmentAssessment, User

from .questions import get_questions
from .schemas import (
    AssessmentQuestionsResponse,
    AssessmentResultResponse,
    QuestionResponse,
    SubmitAssessmentRequest,
)
from .scoring import ScoringError, calculate_full_assessment

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_dev"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create router
router = APIRouter(prefix="/api/attachment", tags=["attachment"])

# Retake cooldown period (90 days as per GDPR best practices)
RETAKE_COOLDOWN_DAYS = 90


def get_db() -> Session:
    """Database session dependency.

    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from access token.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Import here to avoid circular dependency
    from backend.services.auth.security import get_user_id_from_token, verify_token_type

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if not verify_token_type(token, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.get(
    "/assessment",
    response_model=AssessmentQuestionsResponse,
    summary="Get attachment assessment questions",
    description=(
        "Retrieve the 25-question ECR-R attachment assessment. "
        "Questions measure anxiety and avoidance dimensions on a 1-7 Likert scale."
    ),
)
async def get_assessment_questions() -> AssessmentQuestionsResponse:
    """Get all 25 attachment assessment questions.

    Returns:
        Assessment questions with instructions and scale

    Example:
        GET /api/attachment/assessment
        Returns:
        {
            "questions": [
                {"id": 1, "text": "I'm afraid that I will lose my partner's love."},
                ...
            ],
            "instructions": "Please rate each statement...",
            "scale": {1: "Strongly Disagree", ..., 7: "Strongly Agree"}
        }
    """
    questions_data = get_questions()
    questions = [QuestionResponse(**q) for q in questions_data]

    return AssessmentQuestionsResponse(questions=questions)


@router.post(
    "/assessment",
    response_model=AssessmentResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit attachment assessment responses",
    description=(
        "Submit responses to the attachment assessment and receive results. "
        "Requires explicit consent for processing psychological data (GDPR Article 9). "
        "Users can retake after 90 days."
    ),
)
async def submit_assessment(
    request: SubmitAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResultResponse:
    """Submit attachment assessment and get results.

    Args:
        request: Assessment responses (25 questions) with consent
        current_user: Authenticated user
        db: Database session

    Returns:
        Assessment results with attachment style and insights

    Raises:
        HTTPException: If consent not given, validation fails, or retake too soon
    """
    # Check if user can retake (90-day cooldown)
    stmt = select(AttachmentAssessment).where(
        AttachmentAssessment.user_id == current_user.id
    )
    result = db.execute(stmt)
    existing_assessment = result.scalar_one_or_none()

    if existing_assessment is not None:
        time_since_last = datetime.utcnow() - existing_assessment.created_at.replace(
            tzinfo=None
        )
        cooldown_period = timedelta(days=RETAKE_COOLDOWN_DAYS)

        if time_since_last < cooldown_period:
            days_remaining = (cooldown_period - time_since_last).days
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Assessment can be retaken after {RETAKE_COOLDOWN_DAYS} days. "
                    f"Please wait {days_remaining} more days."
                ),
            )

    # Convert responses to scoring format
    responses_dict = {r.question_id: r.response_value for r in request.responses}

    # Calculate assessment results
    try:
        results = calculate_full_assessment(responses_dict)
    except ScoringError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scoring error: {str(e)}",
        ) from e

    # Create or update assessment record
    if existing_assessment:
        # Update existing record (retake after cooldown)
        existing_assessment.anxiety_score = results["anxiety_score"]
        existing_assessment.avoidance_score = results["avoidance_score"]
        existing_assessment.style = results["attachment_style"]
        existing_assessment.updated_at = datetime.utcnow()
        assessment = existing_assessment
    else:
        # Create new assessment
        assessment = AttachmentAssessment(
            user_id=current_user.id,
            anxiety_score=results["anxiety_score"],
            avoidance_score=results["avoidance_score"],
            style=results["attachment_style"],
            assessment_version="1.0",
            total_questions=25,
        )
        db.add(assessment)

    db.commit()
    db.refresh(assessment)

    # Calculate next retake date
    next_retake_date = assessment.created_at + timedelta(days=RETAKE_COOLDOWN_DAYS)
    can_retake = datetime.utcnow() >= next_retake_date.replace(tzinfo=None)

    return AssessmentResultResponse(
        id=assessment.id,
        user_id=assessment.user_id,
        anxiety_score=assessment.anxiety_score,
        avoidance_score=assessment.avoidance_score,
        attachment_style=assessment.style,
        insight=results["insight"],
        assessment_version=assessment.assessment_version,
        created_at=assessment.created_at,
        can_retake=can_retake,
        next_retake_date=next_retake_date if not can_retake else None,
    )


@router.get(
    "/results/{user_id}",
    response_model=AssessmentResultResponse,
    summary="Get attachment assessment results",
    description=(
        "Retrieve a user's attachment assessment results. "
        "Only the user themselves can access their results."
    ),
)
async def get_assessment_results(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResultResponse:
    """Get attachment assessment results for a user.

    Args:
        user_id: User ID to get results for
        current_user: Authenticated user
        db: Database session

    Returns:
        Assessment results if found

    Raises:
        HTTPException: If user tries to access another user's results or no results found
    """
    # Only allow users to access their own results (privacy)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own assessment results",
        )

    # Fetch assessment from database
    stmt = select(AttachmentAssessment).where(AttachmentAssessment.user_id == user_id)
    result = db.execute(stmt)
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment found for this user",
        )

    # Get fresh insight based on current style
    from .scoring import get_attachment_insight

    insight = get_attachment_insight(assessment.style)

    # Calculate retake eligibility
    next_retake_date = assessment.created_at + timedelta(days=RETAKE_COOLDOWN_DAYS)
    can_retake = datetime.utcnow() >= next_retake_date.replace(tzinfo=None)

    return AssessmentResultResponse(
        id=assessment.id,
        user_id=assessment.user_id,
        anxiety_score=assessment.anxiety_score,
        avoidance_score=assessment.avoidance_score,
        attachment_style=assessment.style,
        insight=insight,
        assessment_version=assessment.assessment_version,
        created_at=assessment.created_at,
        can_retake=can_retake,
        next_retake_date=next_retake_date if not can_retake else None,
    )


__all__ = ["router"]
