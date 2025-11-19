"""
Push notification service for offline message delivery.

Handles APNs (iOS) and FCM (Android) push notifications.
"""

import logging
import os
from uuid import UUID

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service for sending push notifications to offline users.

    Supports both APNs (iOS) and FCM (Android/Web).
    """

    def __init__(self) -> None:
        """Initialize push notification service."""
        self.apns_enabled = bool(os.getenv("APNS_KEY_ID"))
        self.fcm_enabled = bool(os.getenv("FCM_SERVER_KEY"))

        if not (self.apns_enabled or self.fcm_enabled):
            logger.warning(
                "Push notification credentials not configured. "
                "Notifications will be logged but not sent."
            )

    async def send_message_notification(
        self, user_id: UUID, sender_name: str, message_preview: str
    ) -> bool:
        """
        Send push notification for a new message.

        Args:
            user_id: ID of the user to notify
            sender_name: Name of the message sender
            message_preview: Preview of the message content (first 50 chars)

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # In production, get user's device tokens from database
            # and send via APNs/FCM
            logger.info(
                f"Push notification for user {user_id}: "
                f"New message from {sender_name}: {message_preview}"
            )

            # Mock implementation - always succeeds
            return True

        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    async def send_match_notification(self, user_id: UUID, match_name: str) -> bool:
        """
        Send push notification for a new match.

        Args:
            user_id: ID of the user to notify
            match_name: Name of the new match

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            logger.info(f"Push notification for user {user_id}: " f"New match with {match_name}!")

            return True

        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    async def send_apns_notification(
        self, device_token: str, title: str, body: str, data: dict | None = None
    ) -> bool:
        """
        Send notification via Apple Push Notification Service.

        Args:
            device_token: APNs device token
            title: Notification title
            body: Notification body
            data: Optional additional data

        Returns:
            True if sent successfully
        """
        if not self.apns_enabled:
            logger.debug("APNs not configured, skipping iOS notification")
            return False

        try:
            # In production: Use aioapns or similar library
            logger.info(f"APNs notification: {title} - {body}")
            return True

        except Exception as e:
            logger.error(f"Error sending APNs notification: {e}")
            return False

    async def send_fcm_notification(
        self, device_token: str, title: str, body: str, data: dict | None = None
    ) -> bool:
        """
        Send notification via Firebase Cloud Messaging.

        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional additional data

        Returns:
            True if sent successfully
        """
        if not self.fcm_enabled:
            logger.debug("FCM not configured, skipping Android notification")
            return False

        try:
            # In production: Use aiofcm or similar library
            logger.info(f"FCM notification: {title} - {body}")
            return True

        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return False


# Singleton instance
_notification_service: PushNotificationService | None = None


def get_notification_service() -> PushNotificationService:
    """
    Get or create the push notification service singleton.

    Returns:
        PushNotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = PushNotificationService()
    return _notification_service
