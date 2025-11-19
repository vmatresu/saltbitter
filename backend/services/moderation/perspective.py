"""Perspective API integration for text content moderation."""

import os
from typing import Any

from googleapiclient import discovery  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore

from .schemas import PerspectiveScore, TextScreenRequest, TextScreenResponse

# Moderation thresholds (from task specification)
AUTO_BLOCK_THRESHOLD = 0.85
MANUAL_REVIEW_THRESHOLD = 0.70

# Attributes to analyze with Perspective API
PERSPECTIVE_ATTRIBUTES = [
    "TOXICITY",
    "SEVERE_TOXICITY",
    "IDENTITY_ATTACK",
    "THREAT",
    "SEXUALLY_EXPLICIT",
    "PROFANITY",
]


class PerspectiveClient:
    """
    Client for Google Perspective API.

    Screens text content for toxicity and other harmful attributes.
    """

    def __init__(self) -> None:
        """Initialize Perspective API client."""
        api_key = os.getenv("PERSPECTIVE_API_KEY")
        if not api_key:
            raise ValueError("PERSPECTIVE_API_KEY environment variable not set")

        self.client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=api_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

    def analyze_text(self, text: str) -> dict[str, Any]:
        """
        Analyze text using Perspective API.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary of attribute scores

        Raises:
            HttpError: If API request fails
        """
        analyze_request = {
            "comment": {"text": text},
            "languages": ["en"],
            "requestedAttributes": {attr: {} for attr in PERSPECTIVE_ATTRIBUTES},
        }

        try:
            response = self.client.comments().analyze(body=analyze_request).execute()
            return response.get("attributeScores", {})
        except HttpError as e:
            # Log error and return empty scores rather than failing
            print(f"Perspective API error: {e}")
            return {}

    def screen_text(self, request: TextScreenRequest) -> TextScreenResponse:
        """
        Screen text content and determine if it should be allowed, flagged, or blocked.

        Args:
            request: Text screening request

        Returns:
            TextScreenResponse with decision and scores
        """
        # Analyze text
        attribute_scores = self.analyze_text(request.text)

        # Convert to PerspectiveScore objects
        scores: dict[str, PerspectiveScore] = {}
        max_score = 0.0

        for attr, data in attribute_scores.items():
            summary_score = data.get("summaryScore", {}).get("value", 0.0)
            span_scores = data.get("spanScores", [])

            # Get the highest span score
            score = max([s.get("score", {}).get("value", 0.0) for s in span_scores], default=0.0)

            scores[attr] = PerspectiveScore(score=score, summary_score=summary_score)

            # Track maximum score across all attributes
            max_score = max(max_score, summary_score)

        # Determine action based on thresholds
        auto_blocked = max_score >= AUTO_BLOCK_THRESHOLD
        flagged = AUTO_BLOCK_THRESHOLD > max_score >= MANUAL_REVIEW_THRESHOLD
        allowed = not auto_blocked

        # Generate reason
        reason = None
        if auto_blocked:
            # Find which attribute(s) caused the block
            blocked_attrs = [
                attr
                for attr, score_obj in scores.items()
                if score_obj.summary_score >= AUTO_BLOCK_THRESHOLD
            ]
            reason = f"Content auto-blocked due to high {', '.join(blocked_attrs).lower()} score"
        elif flagged:
            flagged_attrs = [
                attr
                for attr, score_obj in scores.items()
                if score_obj.summary_score >= MANUAL_REVIEW_THRESHOLD
            ]
            reason = (
                f"Content flagged for manual review due to {', '.join(flagged_attrs).lower()}"
            )

        return TextScreenResponse(
            allowed=allowed,
            flagged=flagged,
            auto_blocked=auto_blocked,
            overall_score=max_score,
            scores=scores,
            reason=reason,
        )


# Global client instance (lazy initialization)
_perspective_client: PerspectiveClient | None = None


def get_perspective_client() -> PerspectiveClient:
    """
    Get or create Perspective API client instance.

    Returns:
        PerspectiveClient instance
    """
    global _perspective_client
    if _perspective_client is None:
        _perspective_client = PerspectiveClient()
    return _perspective_client
