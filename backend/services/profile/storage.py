"""
S3 storage service for profile photos.

Handles photo uploads, deletions, face detection via AWS Rekognition,
and URL generation with CloudFront CDN support.
"""

import io
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image

# S3 Configuration from environment
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "saltbitter-dev")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")  # Optional for production

# AWS Rekognition Configuration (optional for development)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Photo validation constants
MAX_PHOTO_SIZE_MB = 10
MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024
MIN_PHOTO_DIMENSION = 800
ALLOWED_FORMATS = {"JPEG", "PNG", "JPG"}
FACE_DETECTION_CONFIDENCE_THRESHOLD = 80.0


class StorageService:
    """Service for managing photo storage in S3."""

    def __init__(self) -> None:
        """Initialize S3 and Rekognition clients."""
        # Initialize S3 client
        s3_config = {
            "service_name": "s3",
            "endpoint_url": S3_ENDPOINT,
            "aws_access_key_id": S3_ACCESS_KEY,
            "aws_secret_access_key": S3_SECRET_KEY,
            "region_name": S3_REGION,
        }

        # For production AWS, remove endpoint_url
        if S3_ENDPOINT and ("amazonaws.com" in S3_ENDPOINT or not S3_ENDPOINT.startswith("http")):
            del s3_config["endpoint_url"]

        self.s3_client = boto3.client(**s3_config)
        self.bucket_name = S3_BUCKET

        # Initialize Rekognition client if AWS credentials are available
        self.rekognition_client: Optional[boto3.client] = None
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            try:
                self.rekognition_client = boto3.client(
                    "rekognition",
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=S3_REGION,
                )
            except (ClientError, NoCredentialsError):
                # Rekognition is optional for development
                self.rekognition_client = None

    def validate_image(self, file_bytes: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file.

        Args:
            file_bytes: Image file content as bytes
            filename: Original filename

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if len(file_bytes) > MAX_PHOTO_SIZE_BYTES:
            return False, f"File size exceeds {MAX_PHOTO_SIZE_MB}MB limit"

        # Check file format and dimensions
        try:
            img = Image.open(io.BytesIO(file_bytes))

            # Check format
            if img.format not in ALLOWED_FORMATS:
                return False, f"Format must be one of: {', '.join(ALLOWED_FORMATS)}"

            # Check dimensions
            width, height = img.size
            if width < MIN_PHOTO_DIMENSION or height < MIN_PHOTO_DIMENSION:
                return False, f"Image dimensions must be at least {MIN_PHOTO_DIMENSION}x{MIN_PHOTO_DIMENSION}px"

            return True, None

        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    async def detect_faces(self, file_bytes: bytes) -> Tuple[bool, Optional[float]]:
        """
        Detect faces in image using AWS Rekognition.

        Args:
            file_bytes: Image file content as bytes

        Returns:
            Tuple of (face_detected, confidence)
        """
        if not self.rekognition_client:
            # If Rekognition is not configured, return True to allow uploads in development
            return True, None

        try:
            response = self.rekognition_client.detect_faces(
                Image={"Bytes": file_bytes}, Attributes=["DEFAULT"]
            )

            faces = response.get("FaceDetails", [])
            if not faces:
                return False, 0.0

            # Get highest confidence face
            highest_confidence = max(face["Confidence"] for face in faces)

            # Check if confidence meets threshold
            face_detected = highest_confidence >= FACE_DETECTION_CONFIDENCE_THRESHOLD
            return face_detected, highest_confidence

        except ClientError as e:
            # Log error but don't fail upload
            print(f"Rekognition error: {e}")
            return True, None

    async def upload_photo(
        self,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg",
    ) -> Tuple[str, str]:
        """
        Upload photo to S3.

        Args:
            user_id: User UUID
            file_bytes: Image file content as bytes
            filename: Original filename
            content_type: MIME type of the image

        Returns:
            Tuple of (photo_id, photo_url)

        Raises:
            ValueError: If validation fails
            Exception: If upload fails
        """
        # Validate image
        is_valid, error_msg = self.validate_image(file_bytes, filename)
        if not is_valid:
            raise ValueError(error_msg)

        # Generate unique photo ID
        photo_id = str(uuid.uuid4())
        file_extension = filename.rsplit(".", 1)[-1].lower()
        s3_key = f"profiles/{user_id}/photos/{photo_id}.{file_extension}"

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
                Metadata={
                    "user_id": user_id,
                    "photo_id": photo_id,
                    "uploaded_at": datetime.utcnow().isoformat(),
                },
            )

            # Generate URL
            photo_url = self._generate_photo_url(s3_key)

            return photo_id, photo_url

        except ClientError as e:
            raise Exception(f"Failed to upload photo: {str(e)}")

    async def delete_photo(self, user_id: str, photo_id: str, file_extension: str = "jpg") -> bool:
        """
        Delete photo from S3.

        Args:
            user_id: User UUID
            photo_id: Photo UUID
            file_extension: File extension (jpg, png, etc.)

        Returns:
            True if deleted successfully

        Raises:
            Exception: If deletion fails
        """
        s3_key = f"profiles/{user_id}/photos/{photo_id}.{file_extension}"

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True

        except ClientError as e:
            raise Exception(f"Failed to delete photo: {str(e)}")

    def _generate_photo_url(self, s3_key: str) -> str:
        """
        Generate photo URL.

        Uses CloudFront if configured, otherwise generates S3 URL.

        Args:
            s3_key: S3 object key

        Returns:
            Photo URL (CloudFront or S3)
        """
        if CLOUDFRONT_DOMAIN:
            # Use CloudFront CDN
            return f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
        else:
            # Use S3 URL (for development with MinIO)
            if S3_ENDPOINT.startswith("http://") or S3_ENDPOINT.startswith("https://"):
                return f"{S3_ENDPOINT}/{self.bucket_name}/{s3_key}"
            else:
                return f"https://{self.bucket_name}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

    async def get_photo_count(self, user_id: str) -> int:
        """
        Get count of photos for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of photos
        """
        prefix = f"profiles/{user_id}/photos/"

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return int(response.get("KeyCount", 0))

        except ClientError:
            return 0


# Global storage service instance
storage_service = StorageService()
