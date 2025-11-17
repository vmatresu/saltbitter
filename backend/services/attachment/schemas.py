"""
Pydantic schemas for attachment assessment API.

Request and response models for attachment assessment endpoints.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


AttachmentStyle = Literal["Secure", "Anxious", "Avoidant", "Fearful-Avoidant"]


class QuestionResponse(BaseModel):
    """Single question in assessment."""

    id: int = Field(..., ge=1, le=25, description="Question ID (1-25)")
    text: str = Field(..., description="Question text")

    model_config = {"from_attributes": True}


class AssessmentQuestionsResponse(BaseModel):
    """Response containing all assessment questions."""

    questions: list[QuestionResponse] = Field(..., description="List of 25 questions")
    instructions: str = Field(
        default=(
            "Please rate each statement on a scale from 1 (Strongly Disagree) to 7 (Strongly Agree), "
            "thinking about how you generally experience romantic relationships."
        ),
        description="Instructions for taking the assessment",
    )
    scale: dict[int, str] = Field(
        default={
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Slightly Disagree",
            4: "Neutral",
            5: "Slightly Agree",
            6: "Agree",
            7: "Strongly Agree",
        },
        description="Likert scale labels",
    )

    model_config = {"from_attributes": True}


class AssessmentResponse(BaseModel):
    """User's response to a single question."""

    question_id: int = Field(..., ge=1, le=25, description="Question ID (1-25)")
    response_value: int = Field(
        ..., ge=1, le=7, description="Response value on 1-7 Likert scale"
    )

    model_config = {"from_attributes": True}


class SubmitAssessmentRequest(BaseModel):
    """Request to submit assessment responses."""

    responses: list[AssessmentResponse] = Field(
        ..., min_length=25, max_length=25, description="All 25 question responses"
    )
    consent_given: bool = Field(
        ...,
        description=(
            "User consent for processing psychological assessment data (GDPR Article 9)"
        ),
    )

    @field_validator("consent_given")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        """Validate that consent is explicitly given."""
        if not v:
            raise ValueError(
                "Explicit consent is required to process psychological assessment data"
            )
        return v

    @field_validator("responses")
    @classmethod
    def validate_all_questions_answered(
        cls, v: list[AssessmentResponse]
    ) -> list[AssessmentResponse]:
        """Validate that all 25 questions are answered exactly once."""
        question_ids = [r.question_id for r in v]

        # Check for duplicates
        if len(question_ids) != len(set(question_ids)):
            duplicates = [qid for qid in question_ids if question_ids.count(qid) > 1]
            raise ValueError(f"Duplicate responses for questions: {set(duplicates)}")

        # Check all questions 1-25 are present
        expected_ids = set(range(1, 26))
        provided_ids = set(question_ids)

        if provided_ids != expected_ids:
            missing = expected_ids - provided_ids
            raise ValueError(f"Missing responses for questions: {sorted(missing)}")

        return v

    model_config = {"from_attributes": True}


class AssessmentResultResponse(BaseModel):
    """Assessment results with attachment style and scores."""

    id: UUID = Field(..., description="Assessment record ID")
    user_id: UUID = Field(..., description="User ID")
    anxiety_score: float = Field(
        ..., ge=1.0, le=7.0, description="Anxiety dimension score (1.0-7.0)"
    )
    avoidance_score: float = Field(
        ..., ge=1.0, le=7.0, description="Avoidance dimension score (1.0-7.0)"
    )
    attachment_style: AttachmentStyle = Field(
        ..., description="Classified attachment style"
    )
    insight: str = Field(
        ..., description="Interpretive insight about the attachment style"
    )
    assessment_version: str = Field(
        default="1.0", description="Assessment version for tracking changes"
    )
    created_at: datetime = Field(..., description="When assessment was taken")
    can_retake: bool = Field(
        ..., description="Whether user can retake (90-day cooldown)"
    )
    next_retake_date: datetime | None = Field(
        None, description="Date when user can retake assessment (if applicable)"
    )

    model_config = {"from_attributes": True}


class ConsentRequest(BaseModel):
    """Request to record user consent for assessment."""

    consent_given: bool = Field(
        ...,
        description="User consent for processing psychological data",
    )
    understand_usage: bool = Field(
        ...,
        description=(
            "User confirms understanding of how psychological data will be used"
        ),
    )

    @field_validator("consent_given", "understand_usage")
    @classmethod
    def validate_both_true(cls, v: bool) -> bool:
        """Validate that both consent fields are true."""
        if not v:
            raise ValueError("Both consent and understanding confirmation are required")
        return v

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error response for validation failures."""

    detail: str = Field(..., description="Error message")
    error_code: str | None = Field(None, description="Error code for client handling")

    model_config = {"from_attributes": True}


__all__ = [
    "QuestionResponse",
    "AssessmentQuestionsResponse",
    "AssessmentResponse",
    "SubmitAssessmentRequest",
    "AssessmentResultResponse",
    "ConsentRequest",
    "ErrorResponse",
]
