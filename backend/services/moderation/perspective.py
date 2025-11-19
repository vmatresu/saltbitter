"""
Perspective API integration for text content moderation.

Uses Google's Perspective API to detect toxic, harmful, or inappropriate content
in messages, bios, and other user-generated text.
"""

import os
from typing import Dict

import httpx
from fastapi import HTTPException, status


class PerspectiveAPIClient:
    """
    Client for Google Perspective API.

    Analyzes text content for various toxicity attributes including:
    - TOXICITY
    - SEVERE_TOXICITY
    - IDENTITY_ATTACK
    - THREAT
    - SEXUALLY_EXPLICIT
    - PROFANITY
    """

    # Attribute names as defined by Perspective API
    ATTRIBUTES = [
        "TOXICITY",
        "SEVERE_TOXICITY",
        "IDENTITY_ATTACK",
        "THREAT",
        "SEXUALLY_EXPLICIT",
        "PROFANITY",
    ]

    # Moderation thresholds
    AUTO_BLOCK_THRESHOLD = 0.85  # Block automatically
    MANUAL_REVIEW_THRESHOLD = 0.70  # Send to review queue

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Perspective API client.

        Args:
            api_key: Google Perspective API key (defaults to env var)

        Raises:
            ValueError: If API key not provided
        """
        self.api_key = api_key or os.getenv("PERSPECTIVE_API_KEY")
        if not self.api_key:
            raise ValueError("PERSPECTIVE_API_KEY must be set")

        self.base_url = "https://commentanalyzer.googleapis.com/v1alpha1"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def analyze_text(self, text: str, language: str = "en") -> Dict[str, float]:
        """
        Analyze text content for toxicity scores.

        Args:
            text: Text content to analyze
            language: Language code (default: 'en')

        Returns:
            Dictionary mapping attribute names to scores (0.0 - 1.0)

        Raises:
            HTTPException: If API call fails

        Example:
            >>> client = PerspectiveAPIClient()
            >>> scores = await client.analyze_text("Hello, nice to meet you!")
            >>> scores["TOXICITY"]
            0.05
        """
        if not text or len(text.strip()) == 0:
            # Empty text gets neutral scores
            return {attr: 0.0 for attr in self.ATTRIBUTES}

        # Truncate very long text
        if len(text) > 20000:
            text = text[:20000]

        try:
            request_data = {
                "comment": {"text": text},
                "languages": [language],
                "requestedAttributes": {attr: {} for attr in self.ATTRIBUTES},
            }

            response = await self.client.post(
                f"{self.base_url}/comments:analyze",
                params={"key": self.api_key},
                json=request_data,
            )

            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Perspective API error: {error_detail}",
                )

            result = response.json()
            attribute_scores = result.get("attributeScores", {})

            # Extract summary scores
            scores = {}
            for attr in self.ATTRIBUTES:
                if attr in attribute_scores:
                    scores[attr] = attribute_scores[attr]["summaryScore"]["value"]
                else:
                    scores[attr] = 0.0

            return scores

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to Perspective API: {str(e)}",
            ) from e

    def should_auto_block(self, scores: Dict[str, float]) -> bool:
        """
        Determine if content should be auto-blocked.

        Args:
            scores: Attribute scores from analyze_text()

        Returns:
            True if any score exceeds auto-block threshold

        Example:
            >>> scores = {"TOXICITY": 0.90, "THREAT": 0.05}
            >>> client.should_auto_block(scores)
            True
        """
        return any(score >= self.AUTO_BLOCK_THRESHOLD for score in scores.values())

    def should_manual_review(self, scores: Dict[str, float]) -> bool:
        """
        Determine if content should go to manual review queue.

        Args:
            scores: Attribute scores from analyze_text()

        Returns:
            True if any score exceeds manual review threshold but not auto-block

        Example:
            >>> scores = {"TOXICITY": 0.75, "THREAT": 0.05}
            >>> client.should_manual_review(scores)
            True
        """
        if self.should_auto_block(scores):
            return False  # Auto-blocked, no need for review

        return any(score >= self.MANUAL_REVIEW_THRESHOLD for score in scores.values())

    def get_max_score(self, scores: Dict[str, float]) -> float:
        """
        Get the maximum toxicity score.

        Args:
            scores: Attribute scores from analyze_text()

        Returns:
            Highest score value

        Example:
            >>> scores = {"TOXICITY": 0.75, "THREAT": 0.90}
            >>> client.get_max_score(scores)
            0.90
        """
        return max(scores.values()) if scores else 0.0

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
