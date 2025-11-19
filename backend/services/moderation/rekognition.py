"""
AWS Rekognition integration for photo content moderation.

Uses AWS Rekognition to detect inappropriate content in user-uploaded photos.
"""

import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status


class RekognitionClient:
    """
    Client for AWS Rekognition content moderation.

    Analyzes photos for inappropriate or unsafe content including:
    - Explicit nudity
    - Suggestive content
    - Graphic violence or gore
    - Drugs, tobacco, alcohol
    - Hate symbols
    - Rude gestures
    """

    # Moderation thresholds
    AUTO_BLOCK_CONFIDENCE = 85.0  # Block if any unsafe label >= 85% confidence
    MANUAL_REVIEW_CONFIDENCE = 70.0  # Review if any unsafe label >= 70% confidence

    # Categories to flag
    UNSAFE_CATEGORIES = [
        "Explicit Nudity",
        "Suggestive",
        "Violence",
        "Visually Disturbing",
        "Rude Gestures",
        "Drugs",
        "Tobacco",
        "Alcohol",
        "Gambling",
        "Hate Symbols",
    ]

    def __init__(
        self,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
    ) -> None:
        """
        Initialize AWS Rekognition client.

        Args:
            aws_access_key_id: AWS access key (defaults to env var)
            aws_secret_access_key: AWS secret key (defaults to env var)
            region_name: AWS region (defaults to env var or 'us-east-1')
        """
        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region_name or os.getenv("AWS_REGION", "us-east-1"),
        )

    async def detect_moderation_labels(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect moderation labels in image.

        Args:
            image_bytes: Image file as bytes

        Returns:
            Dictionary containing moderation labels and metadata

        Raises:
            HTTPException: If AWS API call fails

        Example:
            >>> client = RekognitionClient()
            >>> with open("photo.jpg", "rb") as f:
            ...     result = await client.detect_moderation_labels(f.read())
            >>> result["unsafe"]
            False
        """
        try:
            response = self.client.detect_moderation_labels(Image={"Bytes": image_bytes})

            labels = response.get("ModerationLabels", [])

            # Organize labels by category
            categorized_labels: Dict[str, List[Dict[str, float]]] = {}
            max_confidence = 0.0

            for label in labels:
                name = label.get("Name", "")
                confidence = label.get("Confidence", 0.0)
                parent_name = label.get("ParentName", "")

                # Track highest confidence
                if confidence > max_confidence:
                    max_confidence = confidence

                # Categorize by parent (e.g., "Explicit Nudity" -> various subcategories)
                category = parent_name if parent_name else name
                if category not in categorized_labels:
                    categorized_labels[category] = []

                categorized_labels[category].append({"label": name, "confidence": confidence})

            return {
                "labels": categorized_labels,
                "max_confidence": max_confidence,
                "model_version": response.get("ModerationModelVersion"),
                "raw_labels": labels,  # Keep for audit trail
            }

        except (BotoCoreError, ClientError) as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AWS Rekognition error: {str(e)}",
            ) from e

    def should_auto_block(self, moderation_result: Dict[str, Any]) -> bool:
        """
        Determine if photo should be auto-blocked.

        Args:
            moderation_result: Result from detect_moderation_labels()

        Returns:
            True if any unsafe content detected with high confidence

        Example:
            >>> result = {"max_confidence": 90.0, "labels": {"Explicit Nudity": [...]}}
            >>> client.should_auto_block(result)
            True
        """
        max_confidence = moderation_result.get("max_confidence", 0.0)
        labels = moderation_result.get("labels", {})

        # Auto-block if any unsafe category has high confidence
        if max_confidence >= self.AUTO_BLOCK_CONFIDENCE:
            # Check if it's in an unsafe category
            for category in self.UNSAFE_CATEGORIES:
                if category in labels:
                    return True

        return False

    def should_manual_review(self, moderation_result: Dict[str, Any]) -> bool:
        """
        Determine if photo should go to manual review.

        Args:
            moderation_result: Result from detect_moderation_labels()

        Returns:
            True if potentially unsafe content detected

        Example:
            >>> result = {"max_confidence": 75.0, "labels": {"Suggestive": [...]}}
            >>> client.should_manual_review(result)
            True
        """
        if self.should_auto_block(moderation_result):
            return False  # Auto-blocked, no need for review

        max_confidence = moderation_result.get("max_confidence", 0.0)
        labels = moderation_result.get("labels", {})

        # Send to review if any unsafe category detected
        if max_confidence >= self.MANUAL_REVIEW_CONFIDENCE:
            for category in self.UNSAFE_CATEGORIES:
                if category in labels:
                    return True

        return False

    async def detect_faces(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect faces in image for profile photo validation.

        Args:
            image_bytes: Image file as bytes

        Returns:
            Dictionary with face detection results

        Raises:
            HTTPException: If AWS API call fails

        Example:
            >>> result = await client.detect_faces(image_bytes)
            >>> result["face_count"]
            1
        """
        try:
            response = self.client.detect_faces(
                Image={"Bytes": image_bytes}, Attributes=["DEFAULT"]
            )

            faces = response.get("FaceDetails", [])

            return {
                "face_count": len(faces),
                "faces": faces,
                "has_face": len(faces) > 0,
                "multiple_faces": len(faces) > 1,
            }

        except (BotoCoreError, ClientError) as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AWS Rekognition error: {str(e)}",
            ) from e
