"""AWS Rekognition integration for photo content moderation."""

import os
from typing import Any

import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from .schemas import PhotoScreenRequest, PhotoScreenResponse

# Inappropriate content labels to flag
INAPPROPRIATE_LABELS = [
    "Explicit Nudity",
    "Nudity",
    "Graphic Male Nudity",
    "Graphic Female Nudity",
    "Sexual Activity",
    "Illustrated Explicit Nudity",
    "Adult Toys",
    "Violence",
    "Graphic Violence",
    "Weapons",
    "Drugs",
    "Tobacco",
    "Alcohol",
    "Gambling",
    "Hate Symbols",
]

# Minimum confidence threshold for flagging
MIN_CONFIDENCE = 75.0


class RekognitionClient:
    """
    Client for AWS Rekognition.

    Screens photo content for inappropriate content.
    """

    def __init__(self) -> None:
        """Initialize AWS Rekognition client."""
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not aws_access_key or not aws_secret_key:
            raise ValueError("AWS credentials not configured")

        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
        )

    def detect_moderation_labels(self, image_bytes: bytes) -> list[dict[str, Any]]:
        """
        Detect moderation labels in an image.

        Args:
            image_bytes: Image data as bytes

        Returns:
            List of detected moderation labels

        Raises:
            ClientError: If AWS API request fails
        """
        try:
            response = self.client.detect_moderation_labels(
                Image={"Bytes": image_bytes}, MinConfidence=MIN_CONFIDENCE
            )
            return response.get("ModerationLabels", [])
        except (BotoCoreError, ClientError) as e:
            print(f"Rekognition API error: {e}")
            return []

    def detect_faces(self, image_bytes: bytes) -> list[dict[str, Any]]:
        """
        Detect faces in an image.

        Args:
            image_bytes: Image data as bytes

        Returns:
            List of detected faces

        Raises:
            ClientError: If AWS API request fails
        """
        try:
            response = self.client.detect_faces(
                Image={"Bytes": image_bytes}, Attributes=["DEFAULT"]
            )
            return response.get("FaceDetails", [])
        except (BotoCoreError, ClientError) as e:
            print(f"Rekognition API error: {e}")
            return []

    def screen_photo(self, image_bytes: bytes) -> PhotoScreenResponse:
        """
        Screen photo content and determine if it should be allowed or flagged.

        Args:
            image_bytes: Image data as bytes

        Returns:
            PhotoScreenResponse with decision and detected labels
        """
        # Detect moderation labels
        moderation_labels = self.detect_moderation_labels(image_bytes)

        # Extract label names and confidence
        inappropriate_labels: list[str] = []
        all_labels: list[str] = []
        max_confidence = 0.0

        for label in moderation_labels:
            name = label.get("Name", "")
            confidence = label.get("Confidence", 0.0)
            parent_name = label.get("ParentName")

            all_labels.append(name)
            max_confidence = max(max_confidence, confidence)

            # Check if this is an inappropriate label
            if name in INAPPROPRIATE_LABELS or parent_name in INAPPROPRIATE_LABELS:
                inappropriate_labels.append(name)

        # Determine if photo should be blocked or flagged
        has_inappropriate = len(inappropriate_labels) > 0
        flagged = has_inappropriate and max_confidence >= MIN_CONFIDENCE

        # Photo is allowed if not flagged
        allowed = not flagged

        # Generate reason
        reason = None
        if flagged:
            reason = f"Photo flagged for manual review: detected {', '.join(inappropriate_labels)}"

        return PhotoScreenResponse(
            allowed=allowed,
            flagged=flagged,
            labels=all_labels,
            moderation_labels=inappropriate_labels,
            confidence=max_confidence,
            reason=reason,
        )


# Global client instance (lazy initialization)
_rekognition_client: RekognitionClient | None = None


def get_rekognition_client() -> RekognitionClient:
    """
    Get or create Rekognition client instance.

    Returns:
        RekognitionClient instance
    """
    global _rekognition_client
    if _rekognition_client is None:
        _rekognition_client = RekognitionClient()
    return _rekognition_client
