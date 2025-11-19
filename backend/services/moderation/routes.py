"""FastAPI routes for moderation service."""

import io
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from services.auth.security import get_current_user, require_admin
from services.profile import get_db

from . import blocks, reports, review_queue
from .perspective import get_perspective_client
from .rekognition import get_rekognition_client
from .schemas import (
    AppealResponse,
    BlockResponse,
    CreateAppealRequest,
    CreateBlockRequest,
    CreateReportRequest,
    ModerationStatsResponse,
    PhotoScreenRequest,
    PhotoScreenResponse,
    QueueItemResponse,
    ReportResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    TextScreenRequest,
    TextScreenResponse,
)

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


# Text screening endpoint
@router.post("/screen-text", response_model=TextScreenResponse)
async def screen_text(
    request: TextScreenRequest,
    current_user: User = Depends(get_current_user),
) -> TextScreenResponse:
    """
    Screen text content using Perspective API.

    Analyzes text for toxicity and other harmful attributes.
    Returns decision on whether content should be allowed, flagged, or blocked.
    """
    try:
        perspective = get_perspective_client()
        return perspective.screen_text(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen text: {str(e)}",
        )


# Photo screening endpoint
@router.post("/screen-photo", response_model=PhotoScreenResponse)
async def screen_photo(
    request: PhotoScreenRequest,
    current_user: User = Depends(get_current_user),
) -> PhotoScreenResponse:
    """
    Screen photo content using AWS Rekognition.

    Analyzes photos for inappropriate content.
    Returns decision on whether photo should be allowed or flagged.
    """
    try:
        # Download image from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(request.photo_url)
            response.raise_for_status()
            image_bytes = response.content

        # Screen with Rekognition
        rekognition = get_rekognition_client()
        return rekognition.screen_photo(image_bytes)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download photo: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen photo: {str(e)}",
        )


# User reporting endpoints
@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    Create a user report.

    Allows users to report inappropriate content or behavior.
    """
    try:
        report = await reports.create_report(
            db=db,
            reporter_id=current_user.id,
            reported_user_id=request.reported_user_id,
            content_type=request.content_type,
            reason=request.reason,
            description=request.description,
            content_id=request.content_id,
        )

        return ReportResponse(
            id=report.id,
            status=report.status,
            created_at=report.created_at,
            message="Report created successfully. Our moderation team will review it shortly.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}",
        )


# User blocking endpoints
@router.post("/blocks/{user_id}", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(
    user_id: UUID,
    request: CreateBlockRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockResponse:
    """
    Block a user.

    Prevents the blocked user from seeing your profile or messaging you.
    """
    try:
        # Use user_id from path, but allow override in body for backward compatibility
        blocked_user_id = request.blocked_user_id if request else user_id

        block = await blocks.create_block(
            db=db,
            blocker_id=current_user.id,
            blocked_id=blocked_user_id,
            reason=request.reason if request else None,
        )

        return BlockResponse(
            id=block.id,
            blocker_id=block.blocker_id,
            blocked_id=block.blocked_id,
            created_at=block.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create block: {str(e)}",
        )


@router.delete("/blocks/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_block(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unblock a user.

    Removes the block relationship with the specified user.
    """
    success = await blocks.remove_block(db=db, blocker_id=current_user.id, blocked_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )


# Moderation queue endpoints (admin only)
@router.get("/queue", response_model=list[QueueItemResponse])
async def get_moderation_queue(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[QueueItemResponse]:
    """
    Get pending items from moderation queue.

    Admin endpoint for moderators to review flagged content.
    """
    try:
        items = await review_queue.get_pending_queue(db=db, limit=limit, offset=offset)
        return [QueueItemResponse.model_validate(item) for item in items]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue: {str(e)}",
        )


@router.put("/queue/{item_id}", response_model=ReviewDecisionResponse)
async def review_queue_item(
    item_id: UUID,
    request: ReviewDecisionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ReviewDecisionResponse:
    """
    Review a moderation queue item.

    Admin endpoint for moderators to approve or reject flagged content.
    """
    try:
        item = await review_queue.review_queue_item(
            db=db,
            item_id=item_id,
            moderator_id=current_user.id,
            action=request.action,
            notes=request.notes,
        )

        return ReviewDecisionResponse(
            id=item.id,
            status=item.status,
            action_taken=item.action_taken,
            reviewed_at=item.reviewed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review item: {str(e)}",
        )


# Appeal endpoints
@router.post("/appeals", response_model=AppealResponse, status_code=status.HTTP_201_CREATED)
async def create_appeal(
    request: CreateAppealRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppealResponse:
    """
    Create an appeal for a moderation decision.

    Allows users to appeal actions taken against their content.
    """
    try:
        appeal = await review_queue.create_appeal(
            db=db,
            user_id=current_user.id,
            moderation_queue_id=request.moderation_queue_id,
            reason=request.reason,
            additional_context=request.additional_context,
        )

        return AppealResponse(
            id=appeal.id,
            status=appeal.status,
            created_at=appeal.created_at,
            message="Appeal submitted successfully. We will review it within 24-48 hours.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appeal: {str(e)}",
        )


# Statistics endpoint (admin only)
@router.get("/stats", response_model=ModerationStatsResponse)
async def get_moderation_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ModerationStatsResponse:
    """
    Get moderation statistics.

    Admin endpoint for moderation dashboard.
    """
    try:
        stats = await review_queue.get_moderation_stats(db=db)

        # Get additional stats
        pending_appeals_result = await review_queue.get_pending_appeals(db=db, limit=1000)
        pending_appeals = len(pending_appeals_result)

        pending_reports_result = await reports.get_pending_reports(db=db, limit=1000)
        pending_reports = len(pending_reports_result)

        # Note: We'll need to implement get_active_blocks_count if needed
        active_blocks = 0  # Placeholder

        return ModerationStatsResponse(
            pending_queue_items=stats["pending_queue_items"],
            pending_reports=pending_reports,
            pending_appeals=pending_appeals,
            auto_blocked_today=stats["auto_blocked_today"],
            manual_reviews_today=stats["manual_reviews_today"],
            active_blocks=active_blocks,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )
