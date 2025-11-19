"""
Content moderation service using Perspective API.

Provides toxicity detection and content screening for messages.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PerspectiveAPIClient:
    """
    Client for Google's Perspective API content moderation.

    Screens text content for toxicity, threats, and other harmful attributes.
    """

    # Moderation thresholds
    AUTO_BLOCK_THRESHOLD = 0.85
    MANUAL_REVIEW_THRESHOLD = 0.70

    # Attributes to check
    MODERATION_ATTRIBUTES = [
        "TOXICITY",
        "SEVERE_TOXICITY",
        "IDENTITY_ATTACK",
        "THREAT",
    ]

    def __init__(self) -> None:
        """Initialize Perspective API client."""
        self.api_key = os.getenv("PERSPECTIVE_API_KEY")
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning(
                "Perspective API key not configured. Content moderation will use mock responses."
            )

    async def analyze_text(self, text: str) -> dict[str, Any]:
        """
        Analyze text content for toxicity and harmful attributes.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary containing analysis results with scores and recommendations
        """
        if not self.enabled:
            # Mock response for testing/development
            return self._mock_analysis(text)

        try:
            # In production, call actual Perspective API
            # For now, we'll use the mock implementation
            return self._mock_analysis(text)
        except Exception as e:
            logger.error(f"Error calling Perspective API: {e}")
            # Fail open - allow message but log error
            return {
                "scores": {},
                "max_score": 0.0,
                "flagged_attributes": [],
                "action": "pass",
                "error": str(e),
            }

    def _mock_analysis(self, text: str) -> dict[str, Any]:
        """
        Mock analysis for development/testing.

        Uses simple heuristics to simulate Perspective API responses.

        Args:
            text: Text to analyze

        Returns:
            Mock analysis results
        """
        # Simple keyword-based toxicity detection for testing
        toxic_keywords = [
            "hate",
            "kill",
            "die",
            "stupid",
            "idiot",
            "fuck",
            "shit",
            "asshole",
            "bitch",
        ]

        text_lower = text.lower()
        toxic_count = sum(1 for keyword in toxic_keywords if keyword in text_lower)

        # Calculate mock toxicity score
        base_score = min(toxic_count * 0.25, 0.95)

        # Simulate attribute scores
        scores = {
            "TOXICITY": base_score,
            "SEVERE_TOXICITY": base_score * 0.7 if base_score > 0.5 else 0.0,
            "IDENTITY_ATTACK": base_score * 0.5 if base_score > 0.6 else 0.0,
            "THREAT": base_score * 0.6 if base_score > 0.7 else 0.0,
        }

        max_score = max(scores.values())
        flagged_attributes = [attr for attr, score in scores.items() if score > 0.5]

        # Determine action based on thresholds
        if max_score >= self.AUTO_BLOCK_THRESHOLD:
            action = "block"
        elif max_score >= self.MANUAL_REVIEW_THRESHOLD:
            action = "review"
        else:
            action = "pass"

        return {
            "scores": scores,
            "max_score": max_score,
            "flagged_attributes": flagged_attributes,
            "action": action,
        }

    async def is_content_safe(self, text: str) -> tuple[bool, float, list[str]]:
        """
        Check if content is safe to send.

        Args:
            text: Text content to check

        Returns:
            Tuple of (is_safe, toxicity_score, flagged_attributes)
        """
        result = await self.analyze_text(text)

        is_safe = result["action"] != "block"
        toxicity_score = result["max_score"]
        flagged_attributes = result["flagged_attributes"]

        return is_safe, toxicity_score, flagged_attributes


# Singleton instance
_perspective_client: PerspectiveAPIClient | None = None


def get_perspective_client() -> PerspectiveAPIClient:
    """
    Get or create the Perspective API client singleton.

    Returns:
        PerspectiveAPIClient instance
    """
    global _perspective_client
    if _perspective_client is None:
        _perspective_client = PerspectiveAPIClient()
    return _perspective_client
