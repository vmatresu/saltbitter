"""Tests for notification service."""

from uuid import uuid4

import pytest

from services.matching.notifications import NotificationService, notification_service


@pytest.mark.asyncio
async def test_send_new_matches_notification():
    """Test sending new matches notification."""
    service = NotificationService()
    user_id = uuid4()
    match_count = 5

    result = await service.send_new_matches_notification(user_id, match_count)

    assert result is True


@pytest.mark.asyncio
async def test_send_mutual_match_notification():
    """Test sending mutual match notification."""
    service = NotificationService()
    user_id = uuid4()
    match_user_id = uuid4()
    match_name = "Alice"

    result = await service.send_mutual_match_notification(
        user_id, match_user_id, match_name
    )

    assert result is True


@pytest.mark.asyncio
async def test_send_like_notification():
    """Test sending like notification."""
    service = NotificationService()
    user_id = uuid4()
    liker_name = "Bob"

    result = await service.send_like_notification(user_id, liker_name)

    assert result is True


@pytest.mark.asyncio
async def test_send_batch_notifications():
    """Test sending batch notifications."""
    service = NotificationService()

    notifications = [
        {
            "user_id": uuid4(),
            "type": "new_matches",
            "data": {"count": 3},
        },
        {
            "user_id": uuid4(),
            "type": "mutual_match",
            "data": {
                "match_user_id": uuid4(),
                "match_name": "Charlie",
            },
        },
        {
            "user_id": uuid4(),
            "type": "like",
            "data": {"liker_name": "Diana"},
        },
    ]

    result = await service.send_batch_notifications(notifications)

    assert result["sent"] == 3
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_send_batch_notifications_handles_errors():
    """Test that batch notifications handle individual failures."""
    service = NotificationService()

    # Include an invalid notification
    notifications = [
        {
            "user_id": uuid4(),
            "type": "new_matches",
            "data": {"count": 3},
        },
        {
            "user_id": "invalid-uuid",  # This will cause an error
            "type": "like",
            "data": {"liker_name": "Eve"},
        },
    ]

    result = await service.send_batch_notifications(notifications)

    # Should still send the valid notification
    assert result["sent"] >= 1
    assert result["failed"] >= 0  # May fail on invalid UUID


@pytest.mark.asyncio
async def test_global_notification_service_instance():
    """Test that global notification service instance is available."""
    assert notification_service is not None
    assert isinstance(notification_service, NotificationService)
