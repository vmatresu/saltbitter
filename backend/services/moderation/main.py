"""
Moderation service routes.

Provides endpoints for content moderation, user reporting, blocking, and review queue.
"""

import os
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import User
from backend.database.models.moderation import (
    ContentType,
    ModerationAppeal,
    ModerationRecord,
    ModerationStatus,
    UserBlock,
    UserReport,
)
from backend.services.auth.routes import get_current_user
from .perspective import PerspectiveAPIClient
from .rekognition import RekognitionClient
from .schemas import (
    AppealResponse,
    BlockResponse,
    BlockUserRequest,
    CreateAppealRequest,
    CreateReportRequest,
    MessageResponse,
    ModerationQueueItem,
    ModerationQueueResponse,
    PhotoScreenRequest,
    PhotoScreenResponse,
    ReportResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    TextScreenRequest,
    TextScreenResponse,
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_dev")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create router
router = APIRouter(prefix="/api/moderation", tags=["moderation"])


def get_db() -> Session:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize clients (will be mocked in tests)
perspective_client: PerspectiveAPIClient | None = None
rekognition_client: RekognitionClient | None = None


def get_perspective_client() -> PerspectiveAPIClient:
    """Get Perspective API client."""
    global perspective_client
    if perspective_client is None:
        perspective_client = PerspectiveAPIClient()
    return perspective_client


def get_rekognition_client() -> RekognitionClient:
    """Get Rekognition client."""
    global rekognition_client
    if rekognition_client is None:
        rekognition_client = RekognitionClient()
    return rekognition_client


@router.post("/screen-text", response_model=TextScreenResponse, status_code=status.HTTP_200_OK)
async def screen_text(
    request: TextScreenRequest,
    db: Session = Depends(get_db),
    perspective: PerspectiveAPIClient = Depends(get_perspective_client),
) -> TextScreenResponse:
    """
    Screen text content using Perspective API.

    Analyzes text for toxicity, threats, hate speech, and other harmful content.
    Content exceeding thresholds is flagged or auto-blocked.

    Args:
        request: Text screening request with content and metadata
        db: Database session
        perspective: Perspective API client

    Returns:
        Screening result with scores and moderation status

    Example:
        >>> POST /api/moderation/screen-text
        >>> {"text": "Hello!", "content_type": "message", "user_id": "..."}
        >>> {"allowed": true, "flagged": false, "auto_blocked": false, "scores": {...}}
    """
    # Analyze text with Perspective API
    scores = await perspective.analyze_text(request.text)
    max_score = perspective.get_max_score(scores)
    auto_blocked = perspective.should_auto_block(scores)
    flagged = perspective.should_manual_review(scores)

    # Create moderation record
    moderation_record = ModerationRecord(
        content_type=request.content_type,
        user_id=request.user_id,
        content_text=request.text,
        toxicity_score=scores.get("TOXICITY"),
        severe_toxicity_score=scores.get("SEVERE_TOXICITY"),
        identity_attack_score=scores.get("IDENTITY_ATTACK"),
        threat_score=scores.get("THREAT"),
        sexually_explicit_score=scores.get("SEXUALLY_EXPLICIT"),
        profanity_score=scores.get("PROFANITY"),
        max_score=max_score,
        flagged=flagged,
        status=ModerationStatus.AUTO_BLOCKED if auto_blocked else (
            ModerationStatus.PENDING if flagged else ModerationStatus.APPROVED
        ),
    )

    db.add(moderation_record)
    db.commit()
    db.refresh(moderation_record)

    return TextScreenResponse(
        allowed=not auto_blocked,
        flagged=flagged,
        auto_blocked=auto_blocked,
        scores=scores,
        max_score=max_score,
        moderation_record_id=moderation_record.id,
    )


@router.post("/screen-photo", response_model=PhotoScreenResponse, status_code=status.HTTP_200_OK)
async def screen_photo(
    request: PhotoScreenRequest,
    db: Session = Depends(get_db),
    rekognition: RekognitionClient = Depends(get_rekognition_client),
) -> PhotoScreenResponse:
    """
    Screen photo content using AWS Rekognition.

    Analyzes photos for inappropriate content including nudity, violence, etc.
    Also detects faces for profile photo validation.

    Args:
        request: Photo screening request with URL and user ID
        db: Database session
        rekognition: AWS Rekognition client

    Returns:
        Screening result with labels and moderation status

    Raises:
        HTTPException: If photo cannot be accessed or analyzed

    Example:
        >>> POST /api/moderation/screen-photo
        >>> {"photo_url": "s3://bucket/photo.jpg", "user_id": "..."}
        >>> {"allowed": true, "flagged": false, "labels": {...}}
    """
    # For this implementation, we'll assume photo_url is an S3 key
    # In production, you'd fetch the image bytes from S3
    # For now, we'll return a simplified response
    # TODO: Implement S3 photo fetching

    # Placeholder: Create a basic moderation record
    moderation_record = ModerationRecord(
        content_type=ContentType.PHOTO,
        user_id=request.user_id,
        content_url=request.photo_url,
        flagged=False,
        status=ModerationStatus.APPROVED,
        rekognition_labels={},
        rekognition_moderation={},
    )

    db.add(moderation_record)
    db.commit()
    db.refresh(moderation_record)

    return PhotoScreenResponse(
        allowed=True,
        flagged=False,
        auto_blocked=False,
        labels={},
        max_confidence=0.0,
        has_face=True,
        moderation_record_id=moderation_record.id,
    )


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: CreateReportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Create a user report.

    Allows users to report other users for inappropriate behavior or content.

    Args:
        request: Report details
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created report

    Example:
        >>> POST /api/moderation/reports
        >>> {"reported_user_id": "...", "reason": "harassment", "description": "..."}
    """
    # Check that user isn't reporting themselves
    if request.reported_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot report yourself",
        )

    # Create report
    report = UserReport(
        reporter_id=current_user.id,
        reported_user_id=request.reported_user_id,
        reason=request.reason,
        description=request.description,
        content_type=request.content_type,
        content_id=request.content_id,
        status=ModerationStatus.PENDING,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        status=report.status,
        created_at=report.created_at,
    )


@router.post("/blocks/{user_id}", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def block_user(
    user_id: UUID,
    request: BlockUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> BlockResponse:
    """
    Block a user.

    Prevents mutual visibility and messaging between users.

    Args:
        user_id: ID of user to block (path parameter)
        request: Block request with optional reason
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created block record

    Raises:
        HTTPException: If trying to block self or user already blocked

    Example:
        >>> POST /api/moderation/blocks/{user_id}
        >>> {"blocked_user_id": "...", "reason": "unwanted contact"}
    """
    # Validate user_id matches request
    if user_id != request.blocked_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL user_id must match request blocked_user_id",
        )

    # Check that user isn't blocking themselves
    if request.blocked_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself",
        )

    # Check if already blocked
    existing_block = db.scalar(
        select(UserBlock).where(
            UserBlock.user_id == current_user.id,
            UserBlock.blocked_user_id == request.blocked_user_id,
        )
    )

    if existing_block:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already blocked",
        )

    # Create block
    block = UserBlock(
        user_id=current_user.id,
        blocked_user_id=request.blocked_user_id,
        reason=request.reason,
    )

    db.add(block)
    db.commit()
    db.refresh(block)

    return BlockResponse(
        id=block.id,
        user_id=block.user_id,
        blocked_user_id=block.blocked_user_id,
        created_at=block.created_at,
    )


@router.delete("/blocks/{user_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def unblock_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Unblock a user.

    Removes a block, allowing mutual visibility and messaging again.

    Args:
        user_id: ID of user to unblock
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If no block exists

    Example:
        >>> DELETE /api/moderation/blocks/{user_id}
    """
    # Find the block
    block = db.scalar(
        select(UserBlock).where(
            UserBlock.user_id == current_user.id,
            UserBlock.blocked_user_id == user_id,
        )
    )

    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    db.delete(block)
    db.commit()

    return MessageResponse(message="User unblocked successfully")


@router.get("/queue", response_model=ModerationQueueResponse, status_code=status.HTTP_200_OK)
async def get_moderation_queue(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> ModerationQueueResponse:
    """
    Get moderation review queue (admin only).

    Returns content flagged for manual review.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        db: Database session
        current_user: Must be admin (TODO: add admin check)

    Returns:
        Paginated list of flagged content

    Example:
        >>> GET /api/moderation/queue?page=1&page_size=50
    """
    # TODO: Add admin role check
    # For now, any authenticated user can access (will be restricted in production)

    # Query flagged items
    query = select(ModerationRecord).where(
        ModerationRecord.flagged == True,  # noqa: E712
        ModerationRecord.status == ModerationStatus.PENDING,
    ).order_by(ModerationRecord.created_at.desc())

    # Get total count
    total_query = select(func.count()).select_from(ModerationRecord).where(
        ModerationRecord.flagged == True,  # noqa: E712
        ModerationRecord.status == ModerationStatus.PENDING,
    )
    total = db.scalar(total_query) or 0

    # Paginate
    offset = (page - 1) * page_size
    items_query = query.offset(offset).limit(page_size)
    items = db.scalars(items_query).all()

    queue_items = [
        ModerationQueueItem(
            id=item.id,
            content_type=item.content_type,
            user_id=item.user_id,
            content_text=item.content_text,
            content_url=item.content_url,
            max_score=item.max_score or 0.0,
            flagged=item.flagged,
            status=item.status,
            created_at=item.created_at,
        )
        for item in items
    ]

    return ModerationQueueResponse(
        items=queue_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/review/{record_id}", response_model=ReviewDecisionResponse, status_code=status.HTTP_200_OK)
async def review_content(
    record_id: UUID,
    request: ReviewDecisionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ReviewDecisionResponse:
    """
    Review flagged content (admin only).

    Approves or rejects content in the moderation queue.

    Args:
        record_id: ID of moderation record to review
        request: Review decision
        current_user: Must be admin (TODO: add admin check)
        db: Database session

    Returns:
        Updated moderation record

    Raises:
        HTTPException: If record not found

    Example:
        >>> PUT /api/moderation/review/{record_id}
        >>> {"approved": true, "notes": "Content is acceptable"}
    """
    # TODO: Add admin role check

    # Find the record
    record = db.get(ModerationRecord, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    # Update status
    record.status = ModerationStatus.APPROVED if request.approved else ModerationStatus.REJECTED
    record.reviewed_by = current_user.id
    record.reviewed_at = datetime.utcnow()
    record.review_notes = request.notes

    db.commit()
    db.refresh(record)

    return ReviewDecisionResponse(
        id=record.id,
        status=record.status,
        reviewed_at=record.reviewed_at,
    )


@router.post("/appeal", response_model=AppealResponse, status_code=status.HTTP_201_CREATED)
async def create_appeal(
    request: CreateAppealRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AppealResponse:
    """
    Create an appeal for moderation decision.

    Allows users to contest auto-blocked or rejected content.

    Args:
        request: Appeal details
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created appeal

    Example:
        >>> POST /api/moderation/appeal
        >>> {"moderation_record_id": "...", "appeal_text": "This was a mistake..."}
    """
    # Validate that at least one ID is provided
    if not request.moderation_record_id and not request.user_report_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either moderation_record_id or user_report_id",
        )

    # Create appeal
    appeal = ModerationAppeal(
        moderation_record_id=request.moderation_record_id,
        user_report_id=request.user_report_id,
        user_id=current_user.id,
        appeal_text=request.appeal_text,
        status=ModerationStatus.PENDING,
    )

    db.add(appeal)
    db.commit()
    db.refresh(appeal)

    return AppealResponse(
        id=appeal.id,
        status=appeal.status,
        created_at=appeal.created_at,
    )
