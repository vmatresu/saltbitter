"""
Attachment theory compatibility calculation.

This module implements research-backed attachment style compatibility scoring
based on attachment theory. The algorithm uses anxiety and avoidance scores
to determine attachment styles and calculate compatibility between users.

References:
- Fraley, R. C., & Shaver, P. R. (2000). Adult romantic attachment
- Mikulincer, M., & Shaver, P. R. (2007). Attachment in adulthood
"""

from typing import Literal

AttachmentStyle = Literal["secure", "anxious", "avoidant", "fearful-avoidant"]

# Research-backed compatibility matrix (0-100 scale)
# Based on attachment theory literature about pairing stability
COMPATIBILITY_MATRIX: dict[tuple[AttachmentStyle, AttachmentStyle], float] = {
    # Secure pairings (most stable)
    ("secure", "secure"): 100.0,
    ("secure", "anxious"): 85.0,
    ("secure", "avoidant"): 80.0,
    ("secure", "fearful-avoidant"): 75.0,
    # Anxious pairings
    ("anxious", "secure"): 85.0,
    ("anxious", "anxious"): 65.0,  # Can amplify each other's anxiety
    ("anxious", "avoidant"): 40.0,  # Classic anxious-avoidant trap
    ("anxious", "fearful-avoidant"): 50.0,
    # Avoidant pairings
    ("avoidant", "secure"): 80.0,
    ("avoidant", "anxious"): 40.0,  # Classic anxious-avoidant trap
    ("avoidant", "avoidant"): 70.0,  # Can work with mutual independence
    ("avoidant", "fearful-avoidant"): 55.0,
    # Fearful-avoidant pairings
    ("fearful-avoidant", "secure"): 75.0,
    ("fearful-avoidant", "anxious"): 50.0,
    ("fearful-avoidant", "avoidant"): 55.0,
    ("fearful-avoidant", "fearful-avoidant"): 45.0,
}


def determine_attachment_style(anxiety_score: float, avoidance_score: float) -> AttachmentStyle:
    """
    Determine attachment style from anxiety and avoidance scores.

    Based on two-dimensional model of adult attachment (Bartholomew & Horowitz, 1991):
    - Low anxiety + Low avoidance = Secure
    - High anxiety + Low avoidance = Anxious/Preoccupied
    - Low anxiety + High avoidance = Avoidant/Dismissing
    - High anxiety + High avoidance = Fearful-Avoidant/Disorganized

    Args:
        anxiety_score: Anxiety score (0-100 scale)
        avoidance_score: Avoidance score (0-100 scale)

    Returns:
        AttachmentStyle: One of 'secure', 'anxious', 'avoidant', 'fearful-avoidant'

    Raises:
        ValueError: If scores are outside valid range

    Examples:
        >>> determine_attachment_style(30.0, 25.0)
        'secure'
        >>> determine_attachment_style(75.0, 30.0)
        'anxious'
        >>> determine_attachment_style(25.0, 80.0)
        'avoidant'
        >>> determine_attachment_style(70.0, 75.0)
        'fearful-avoidant'
    """
    if not (0 <= anxiety_score <= 100):
        raise ValueError(f"Anxiety score must be 0-100, got {anxiety_score}")
    if not (0 <= avoidance_score <= 100):
        raise ValueError(f"Avoidance score must be 0-100, got {avoidance_score}")

    # Thresholds based on median split (commonly 50 in research)
    anxiety_threshold = 50.0
    avoidance_threshold = 50.0

    if anxiety_score < anxiety_threshold and avoidance_score < avoidance_threshold:
        return "secure"
    elif anxiety_score >= anxiety_threshold and avoidance_score < avoidance_threshold:
        return "anxious"
    elif anxiety_score < anxiety_threshold and avoidance_score >= avoidance_threshold:
        return "avoidant"
    else:  # Both high
        return "fearful-avoidant"


def calculate_attachment_compatibility(
    style_a: AttachmentStyle, style_b: AttachmentStyle
) -> float:
    """
    Calculate attachment compatibility score between two users.

    Uses research-backed compatibility matrix based on attachment theory.
    The matrix is symmetric (A-B = B-A).

    Args:
        style_a: Attachment style of first user
        style_b: Attachment style of second user

    Returns:
        float: Compatibility score (0-100 scale)

    Examples:
        >>> calculate_attachment_compatibility("secure", "secure")
        100.0
        >>> calculate_attachment_compatibility("anxious", "avoidant")
        40.0
        >>> calculate_attachment_compatibility("avoidant", "anxious")
        40.0
    """
    # Try both orderings since matrix is symmetric
    key = (style_a, style_b)
    if key in COMPATIBILITY_MATRIX:
        return COMPATIBILITY_MATRIX[key]

    # Try reversed order
    key_reversed = (style_b, style_a)
    if key_reversed in COMPATIBILITY_MATRIX:
        return COMPATIBILITY_MATRIX[key_reversed]

    # Default to moderate score if pairing not in matrix (should not happen)
    return 60.0


def calculate_attachment_compatibility_from_scores(
    anxiety_a: float,
    avoidance_a: float,
    anxiety_b: float,
    avoidance_b: float,
) -> tuple[float, AttachmentStyle, AttachmentStyle]:
    """
    Calculate compatibility from raw anxiety/avoidance scores.

    Convenience function that determines styles and calculates compatibility.

    Args:
        anxiety_a: User A's anxiety score (0-100)
        avoidance_a: User A's avoidance score (0-100)
        anxiety_b: User B's anxiety score (0-100)
        avoidance_b: User B's avoidance score (0-100)

    Returns:
        tuple: (compatibility_score, style_a, style_b)

    Examples:
        >>> score, style_a, style_b = calculate_attachment_compatibility_from_scores(
        ...     30.0, 25.0, 35.0, 20.0
        ... )
        >>> score
        100.0
        >>> style_a
        'secure'
        >>> style_b
        'secure'
    """
    style_a = determine_attachment_style(anxiety_a, avoidance_a)
    style_b = determine_attachment_style(anxiety_b, avoidance_b)
    compatibility = calculate_attachment_compatibility(style_a, style_b)

    return compatibility, style_a, style_b
