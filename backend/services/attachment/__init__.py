"""
Attachment assessment service module.

Provides attachment theory assessment functionality including:
- ECR-R 25-question assessment
- Anxiety and avoidance dimension scoring
- Attachment style classification (Secure, Anxious, Avoidant, Fearful-Avoidant)
- GDPR-compliant consent management
- 90-day retake cooldown
"""

from .routes import router as attachment_router
from .schemas import (
    AssessmentQuestionsResponse,
    AssessmentResponse,
    AssessmentResultResponse,
    QuestionResponse,
    SubmitAssessmentRequest,
)
from .scoring import (
    calculate_anxiety_score,
    calculate_avoidance_score,
    calculate_full_assessment,
    classify_attachment_style,
)

__all__ = [
    "attachment_router",
    "AssessmentQuestionsResponse",
    "AssessmentResponse",
    "AssessmentResultResponse",
    "QuestionResponse",
    "SubmitAssessmentRequest",
    "calculate_anxiety_score",
    "calculate_avoidance_score",
    "calculate_full_assessment",
    "classify_attachment_style",
]
