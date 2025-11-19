"""
WebSocket connection management for real-time messaging.

Handles WebSocket connections, message routing, and Redis pub/sub.
"""

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message, User
from .moderation import get_perspective_client
from .notifications import get_notification_service
from .schemas import MessageResponse, WebSocketMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message routing.

    Supports multiple instances via Redis pub/sub for horizontal scaling.
    """

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: dict[UUID, WebSocket] = {}
        self.redis: aioredis.Redis | None = None

    async def connect(self, websocket: WebSocket, user_id: UUID) -> None:
        """
        Accept WebSocket connection and register user.

        Args:
            websocket: WebSocket connection
            user_id: ID of the connecting user
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")

        # Send connection confirmation
        await self.send_message_to_user(
            user_id, WebSocketMessage(type="connection", data={"status": "connected"})
        )

    def disconnect(self, user_id: UUID) -> None:
        """
        Remove WebSocket connection.

        Args:
            user_id: ID of the disconnecting user
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")

    async def send_message_to_user(self, user_id: UUID, message: WebSocketMessage) -> bool:
        """
        Send message to a specific user if connected.

        Args:
            user_id: Target user ID
            message: Message to send

        Returns:
            True if message sent successfully, False if user not connected
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message.model_dump())
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False

    async def broadcast_to_users(self, user_ids: list[UUID], message: WebSocketMessage) -> None:
        """
        Broadcast message to multiple users.

        Args:
            user_ids: List of user IDs to send to
            message: Message to broadcast
        """
        for user_id in user_ids:
            await self.send_message_to_user(user_id, message)

    async def handle_typing_indicator(
        self, from_user_id: UUID, to_user_id: UUID, is_typing: bool
    ) -> None:
        """
        Handle typing indicator event.

        Args:
            from_user_id: User who is typing
            to_user_id: User to notify
            is_typing: Whether user is currently typing
        """
        message = WebSocketMessage(
            type="typing", data={"user_id": str(from_user_id), "is_typing": is_typing}
        )
        await self.send_message_to_user(to_user_id, message)

    async def handle_read_receipt(
        self, message_id: UUID, reader_user_id: UUID, sender_user_id: UUID
    ) -> None:
        """
        Handle read receipt event.

        Args:
            message_id: ID of the message that was read
            reader_user_id: User who read the message
            sender_user_id: User who sent the message (to be notified)
        """
        message = WebSocketMessage(
            type="read",
            data={
                "message_id": str(message_id),
                "read_by": str(reader_user_id),
                "read_at": datetime.utcnow().isoformat(),
            },
        )
        await self.send_message_to_user(sender_user_id, message)


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket_connection(
    websocket: WebSocket, user_id: UUID, db: AsyncSession
) -> None:
    """
    Handle WebSocket connection lifecycle.

    Args:
        websocket: WebSocket connection
        user_id: Authenticated user ID
        db: Database session
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")
            message_data = data.get("data", {})

            if message_type == "message":
                await handle_message_event(user_id, message_data, db)

            elif message_type == "typing":
                to_user_id = UUID(message_data["to_user_id"])
                is_typing = message_data.get("is_typing", False)
                await manager.handle_typing_indicator(user_id, to_user_id, is_typing)

            elif message_type == "read":
                message_id = UUID(message_data["message_id"])
                await handle_read_receipt(message_id, user_id, db)

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {e}")
        manager.disconnect(user_id)


async def handle_message_event(from_user_id: UUID, data: dict[str, Any], db: AsyncSession) -> None:
    """
    Handle incoming message event.

    Args:
        from_user_id: Sender user ID
        data: Message data
        db: Database session
    """
    try:
        to_user_id = UUID(data["to_user_id"])
        content = data["content"]

        # Content moderation
        perspective = get_perspective_client()
        is_safe, toxicity_score, flagged_attributes = await perspective.is_content_safe(content)

        if not is_safe:
            # Send error to sender
            error_message = WebSocketMessage(
                type="error",
                data={
                    "error": "Message blocked due to inappropriate content",
                    "toxicity_score": toxicity_score,
                },
            )
            await manager.send_message_to_user(from_user_id, error_message)
            return

        # Create message in database
        message = Message(from_user_id=from_user_id, to_user_id=to_user_id, content=content)
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Send to recipient if online
        message_response = MessageResponse.model_validate(message)
        ws_message = WebSocketMessage(
            type="message", data=json.loads(message_response.model_dump_json())
        )

        sent_online = await manager.send_message_to_user(to_user_id, ws_message)

        # If recipient offline, send push notification
        if not sent_online:
            notification_service = get_notification_service()

            # Get sender email for notification
            sender_result = await db.execute(select(User).where(User.id == from_user_id))
            sender = sender_result.scalar_one_or_none()

            if sender:
                sender_name = sender.email.split("@")[0]  # Use email prefix as name
                preview = content[:50] + "..." if len(content) > 50 else content
                await notification_service.send_message_notification(
                    to_user_id, sender_name, preview
                )

        # Confirm to sender
        confirmation = WebSocketMessage(
            type="message_sent",
            data={"message_id": str(message.id), "sent_at": message.sent_at.isoformat()},
        )
        await manager.send_message_to_user(from_user_id, confirmation)

    except Exception as e:
        logger.error(f"Error handling message event: {e}")
        error_message = WebSocketMessage(type="error", data={"error": "Failed to send message"})
        await manager.send_message_to_user(from_user_id, error_message)


async def handle_read_receipt(message_id: UUID, reader_user_id: UUID, db: AsyncSession) -> None:
    """
    Handle read receipt event.

    Args:
        message_id: ID of the message that was read
        reader_user_id: User who read the message
        db: Database session
    """
    try:
        # Update message read status
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()

        if message and message.to_user_id == reader_user_id and message.read_at is None:
            message.read_at = datetime.utcnow()
            await db.commit()

            # Notify sender
            await manager.handle_read_receipt(message_id, reader_user_id, message.from_user_id)

    except Exception as e:
        logger.error(f"Error handling read receipt: {e}")
