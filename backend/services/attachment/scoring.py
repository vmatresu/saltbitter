"""
Attachment assessment scoring algorithm.

Implements ECR-R scoring for anxiety and avoidance dimensions,
and classifies attachment styles based on threshold scores.
"""

from typing import Literal

from .questions import (
    ANXIETY_QUESTION_IDS,
    AVOIDANCE_QUESTION_IDS,
    get_question_metadata,
)


AttachmentStyle = Literal["Secure", "Anxious", "Avoidant", "Fearful-Avoidant"]

# Research-validated thresholds for attachment classification
ANXIETY_THRESHOLD = 3.5
AVOIDANCE_THRESHOLD = 3.5

# Valid Likert scale range
MIN_RESPONSE_VALUE = 1
MAX_RESPONSE_VALUE = 7


class ScoringError(Exception):
    """Raised when scoring cannot be completed."""

    pass


def validate_response_value(value: int) -> None:
    """Validate a single response value.

    Args:
        value: Response value to validate

    Raises:
        ScoringError: If value is out of valid range
    """
    if not isinstance(value, int):
        raise ScoringError(f"Response must be an integer, got {type(value)}")

    if value < MIN_RESPONSE_VALUE or value > MAX_RESPONSE_VALUE:
        raise ScoringError(
            f"Response value {value} out of range "
            f"({MIN_RESPONSE_VALUE}-{MAX_RESPONSE_VALUE})"
        )


def validate_responses(responses: dict[int, int]) -> None:
    """Validate all responses are present and valid.

    Args:
        responses: Dictionary mapping question_id to response value

    Raises:
        ScoringError: If responses are invalid or incomplete
    """
    # Check we have exactly 25 responses
    if len(responses) != 25:
        raise ScoringError(f"Expected 25 responses, got {len(responses)}")

    # Check all question IDs are valid (1-25)
    expected_ids = set(range(1, 26))
    provided_ids = set(responses.keys())

    if provided_ids != expected_ids:
        missing = expected_ids - provided_ids
        extra = provided_ids - expected_ids
        error_msg = []
        if missing:
            error_msg.append(f"Missing questions: {sorted(missing)}")
        if extra:
            error_msg.append(f"Invalid question IDs: {sorted(extra)}")
        raise ScoringError("; ".join(error_msg))

    # Validate each response value
    for question_id, value in responses.items():
        try:
            validate_response_value(value)
        except ScoringError as e:
            raise ScoringError(f"Question {question_id}: {e}") from e


def score_response(question_id: int, raw_value: int) -> float:
    """Score a single response, applying reverse scoring if needed.

    Args:
        question_id: Question ID (1-25)
        raw_value: Raw response value (1-7)

    Returns:
        Scored value (may be reversed)

    Raises:
        ScoringError: If question not found
    """
    question = get_question_metadata(question_id)
    if question is None:
        raise ScoringError(f"Question {question_id} not found")

    if question.reverse_scored:
        # Reverse score: 1→7, 2→6, 3→5, 4→4, 5→3, 6→2, 7→1
        return float(8 - raw_value)
    return float(raw_value)


def calculate_anxiety_score(responses: dict[int, int]) -> float:
    """Calculate anxiety dimension score.

    Args:
        responses: Dictionary mapping question_id to response value

    Returns:
        Anxiety score (average of anxiety dimension questions, 1.0-7.0)

    Raises:
        ScoringError: If responses are invalid
    """
    anxiety_scores: list[float] = []

    for question_id in ANXIETY_QUESTION_IDS:
        if question_id not in responses:
            raise ScoringError(f"Missing response for anxiety question {question_id}")

        scored_value = score_response(question_id, responses[question_id])
        anxiety_scores.append(scored_value)

    if not anxiety_scores:
        raise ScoringError("No anxiety questions found")

    return sum(anxiety_scores) / len(anxiety_scores)


def calculate_avoidance_score(responses: dict[int, int]) -> float:
    """Calculate avoidance dimension score.

    Args:
        responses: Dictionary mapping question_id to response value

    Returns:
        Avoidance score (average of avoidance dimension questions, 1.0-7.0)

    Raises:
        ScoringError: If responses are invalid
    """
    avoidance_scores: list[float] = []

    for question_id in AVOIDANCE_QUESTION_IDS:
        if question_id not in responses:
            raise ScoringError(
                f"Missing response for avoidance question {question_id}"
            )

        scored_value = score_response(question_id, responses[question_id])
        avoidance_scores.append(scored_value)

    if not avoidance_scores:
        raise ScoringError("No avoidance questions found")

    return sum(avoidance_scores) / len(avoidance_scores)


def classify_attachment_style(
    anxiety_score: float, avoidance_score: float
) -> AttachmentStyle:
    """Classify attachment style based on anxiety and avoidance scores.

    Based on Brennan, Clark, & Shaver (1998) two-dimensional model:
    - Secure: Low anxiety, low avoidance
    - Anxious (Preoccupied): High anxiety, low avoidance
    - Avoidant (Dismissive): Low anxiety, high avoidance
    - Fearful-Avoidant: High anxiety, high avoidance

    Args:
        anxiety_score: Anxiety dimension score (1.0-7.0)
        avoidance_score: Avoidance dimension score (1.0-7.0)

    Returns:
        Attachment style classification
    """
    high_anxiety = anxiety_score >= ANXIETY_THRESHOLD
    high_avoidance = avoidance_score >= AVOIDANCE_THRESHOLD

    if not high_anxiety and not high_avoidance:
        return "Secure"
    elif high_anxiety and not high_avoidance:
        return "Anxious"
    elif not high_anxiety and high_avoidance:
        return "Avoidant"
    else:  # high_anxiety and high_avoidance
        return "Fearful-Avoidant"


def get_attachment_insight(style: AttachmentStyle) -> str:
    """Get interpretive insight for an attachment style.

    Args:
        style: Attachment style

    Returns:
        Human-readable description and guidance
    """
    insights = {
        "Secure": (
            "You tend to feel comfortable with intimacy and independence. "
            "You generally trust others and feel secure in relationships. "
            "This attachment style is associated with healthy, balanced relationships."
        ),
        "Anxious": (
            "You may seek high levels of intimacy and approval from partners. "
            "You might worry about relationship security and need frequent reassurance. "
            "Being aware of this can help you communicate your needs while building self-confidence."
        ),
        "Avoidant": (
            "You value independence and self-sufficiency highly. "
            "You might feel uncomfortable with too much closeness or emotional expression. "
            "Understanding this can help you gradually build comfort with vulnerability."
        ),
        "Fearful-Avoidant": (
            "You may desire closeness but also fear being hurt or rejected. "
            "This can create internal conflict in relationships. "
            "Recognizing these patterns is an important first step toward healthier connections."
        ),
    }
    return insights[style]


def calculate_full_assessment(
    responses: dict[int, int],
) -> dict[str, float | str]:
    """Calculate complete attachment assessment.

    Args:
        responses: Dictionary mapping question_id (1-25) to response value (1-7)

    Returns:
        Dictionary with anxiety_score, avoidance_score, style, and insight

    Raises:
        ScoringError: If responses are invalid or incomplete
    """
    # Validate all responses
    validate_responses(responses)

    # Calculate dimension scores
    anxiety_score = calculate_anxiety_score(responses)
    avoidance_score = calculate_avoidance_score(responses)

    # Classify attachment style
    style = classify_attachment_style(anxiety_score, avoidance_score)

    # Get insight
    insight = get_attachment_insight(style)

    return {
        "anxiety_score": round(anxiety_score, 2),
        "avoidance_score": round(avoidance_score, 2),
        "attachment_style": style,
        "insight": insight,
    }


__all__ = [
    "ScoringError",
    "validate_responses",
    "calculate_anxiety_score",
    "calculate_avoidance_score",
    "classify_attachment_style",
    "get_attachment_insight",
    "calculate_full_assessment",
    "ANXIETY_THRESHOLD",
    "AVOIDANCE_THRESHOLD",
]
