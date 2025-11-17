"""
Attachment assessment questions.

ECR-R (Experiences in Close Relationships-Revised) questionnaire.
25 validated questions measuring attachment anxiety and avoidance dimensions.
"""

from typing import Literal


AttachmentDimension = Literal["anxiety", "avoidance"]


class Question:
    """Represents a single assessment question."""

    def __init__(
        self,
        id: int,
        text: str,
        dimension: AttachmentDimension,
        reverse_scored: bool = False,
    ):
        """Initialize a question.

        Args:
            id: Question number (1-25)
            text: Question text
            dimension: Which dimension this measures (anxiety or avoidance)
            reverse_scored: If True, reverse the score (8 - response)
        """
        self.id = id
        self.text = text
        self.dimension = dimension
        self.reverse_scored = reverse_scored


# ECR-R 25-question assessment
# Based on validated attachment research (Fraley, Waller, & Brennan, 2000)
ASSESSMENT_QUESTIONS: list[Question] = [
    # Anxiety dimension questions (odd numbers primarily, mixed with avoidance)
    Question(
        1,
        "I'm afraid that I will lose my partner's love.",
        "anxiety",
        False,
    ),
    Question(
        2,
        "I prefer not to show a partner how I feel deep down.",
        "avoidance",
        False,
    ),
    Question(
        3,
        "I often worry that my partner doesn't really care about me.",
        "anxiety",
        False,
    ),
    Question(
        4,
        "I feel comfortable sharing my private thoughts and feelings with my partner.",
        "avoidance",
        True,  # Reverse scored
    ),
    Question(
        5,
        "I often wish that my partner's feelings for me were as strong as my feelings for them.",
        "anxiety",
        False,
    ),
    Question(
        6,
        "I get uncomfortable when a romantic partner wants to be very close.",
        "avoidance",
        False,
    ),
    Question(
        7,
        "I worry a lot about my relationships.",
        "anxiety",
        False,
    ),
    Question(
        8,
        "It helps to turn to my romantic partner in times of need.",
        "avoidance",
        True,  # Reverse scored
    ),
    Question(
        9,
        "I need a lot of reassurance that I am loved by my partner.",
        "anxiety",
        False,
    ),
    Question(
        10,
        "I find it relatively easy to get close to my partner.",
        "avoidance",
        True,  # Reverse scored
    ),
    Question(
        11,
        "Sometimes I feel that I force my partners to show more feeling, more commitment.",
        "anxiety",
        False,
    ),
    Question(
        12,
        "I don't feel comfortable opening up to romantic partners.",
        "avoidance",
        False,
    ),
    Question(
        13,
        "I often worry that my partner will not want to stay with me.",
        "anxiety",
        False,
    ),
    Question(
        14,
        "I prefer not to be too close to romantic partners.",
        "avoidance",
        False,
    ),
    Question(
        15,
        "When I'm not involved in a relationship, I feel somewhat anxious and insecure.",
        "anxiety",
        False,
    ),
    Question(
        16,
        "I find it difficult to allow myself to depend on romantic partners.",
        "avoidance",
        False,
    ),
    Question(
        17,
        "My desire to be very close sometimes scares people away.",
        "anxiety",
        False,
    ),
    Question(
        18,
        "I try to avoid getting too close to my partner.",
        "avoidance",
        False,
    ),
    Question(
        19,
        "I worry that romantic partners won't care about me as much as I care about them.",
        "anxiety",
        False,
    ),
    Question(
        20,
        "I am nervous when partners get too close to me.",
        "avoidance",
        False,
    ),
    Question(
        21,
        "I worry about being abandoned.",
        "anxiety",
        False,
    ),
    Question(
        22,
        "I am very comfortable being close to romantic partners.",
        "avoidance",
        True,  # Reverse scored
    ),
    Question(
        23,
        "I worry that I won't measure up to other people.",
        "anxiety",
        False,
    ),
    Question(
        24,
        "I tell my partner just about everything.",
        "avoidance",
        True,  # Reverse scored
    ),
    Question(
        25,
        "I find that my partner(s) don't want to get as close as I would like.",
        "anxiety",
        False,
    ),
]


def get_questions() -> list[dict[str, str | int]]:
    """Get all assessment questions formatted for API response.

    Returns:
        List of questions with id and text only (no dimension/scoring info)
    """
    return [
        {
            "id": q.id,
            "text": q.text,
        }
        for q in ASSESSMENT_QUESTIONS
    ]


def get_question_metadata(question_id: int) -> Question | None:
    """Get full metadata for a specific question.

    Args:
        question_id: Question ID (1-25)

    Returns:
        Question object or None if not found
    """
    for q in ASSESSMENT_QUESTIONS:
        if q.id == question_id:
            return q
    return None


# Question IDs by dimension for scoring
ANXIETY_QUESTION_IDS = [q.id for q in ASSESSMENT_QUESTIONS if q.dimension == "anxiety"]
AVOIDANCE_QUESTION_IDS = [
    q.id for q in ASSESSMENT_QUESTIONS if q.dimension == "avoidance"
]


__all__ = [
    "Question",
    "ASSESSMENT_QUESTIONS",
    "get_questions",
    "get_question_metadata",
    "ANXIETY_QUESTION_IDS",
    "AVOIDANCE_QUESTION_IDS",
]
