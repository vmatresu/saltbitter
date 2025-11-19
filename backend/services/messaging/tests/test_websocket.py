"""
Comprehensive tests for WebSocket messaging functionality.

Tests cover:
- WebSocket connection management
- Real-time message sending and receiving
- Typing indicators
- Read receipts
- Content moderation
- Error handling
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from database.models import Base, Message, User
from services.auth.security import hash_password
from services.messaging.moderation import PerspectiveAPIClient
from services.messaging.websocket import ConnectionManager, handle_message_event

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_test"
)
TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
async def async_db_engine():
    """Create async test database engine."""
    engine = create_async_engine(TEST_ASYNC_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
async def async_db_session(async_db_engine):
    """Create async test database session."""
    async_session_factory = sessionmaker(
        async_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="user1@example.com",
        password_hash=hash_password("TestPassword123"),
        verified=True,
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session: Session) -> User:
    """Create a second test user."""
    user = User(
        email="user2@example.com",
        password_hash=hash_password("TestPassword123"),
        verified=True,
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager for each test."""
    return ConnectionManager()


# ===== ConnectionManager Tests =====


def test_connection_manager_initialization(connection_manager: ConnectionManager):
    """Test ConnectionManager initializes correctly."""
    assert connection_manager.active_connections == {}
    assert connection_manager.redis is None


def test_connection_manager_disconnect(connection_manager: ConnectionManager):
    """Test disconnecting a user."""
    user_id = uuid4()
    connection_manager.active_connections[user_id] = "mock_websocket"

    connection_manager.disconnect(user_id)

    assert user_id not in connection_manager.active_connections


def test_connection_manager_disconnect_nonexistent(connection_manager: ConnectionManager):
    """Test disconnecting a user that's not connected."""
    user_id = uuid4()
    # Should not raise an error
    connection_manager.disconnect(user_id)
    assert user_id not in connection_manager.active_connections


# ===== Content Moderation Tests =====


@pytest.mark.asyncio
async def test_moderation_safe_content():
    """Test that safe content passes moderation."""
    client = PerspectiveAPIClient()

    is_safe, score, flagged = await client.is_content_safe("Hello, how are you today?")

    assert is_safe is True
    assert score < 0.7
    assert len(flagged) == 0


@pytest.mark.asyncio
async def test_moderation_toxic_content():
    """Test that toxic content is flagged."""
    client = PerspectiveAPIClient()

    is_safe, score, flagged = await client.is_content_safe(
        "I hate you and I hope you die you stupid idiot"
    )

    assert is_safe is False
    assert score >= 0.85
    assert len(flagged) > 0


@pytest.mark.asyncio
async def test_moderation_moderate_content():
    """Test content in the review threshold range."""
    client = PerspectiveAPIClient()

    is_safe, score, flagged = await client.is_content_safe("You're kind of annoying")

    # Should pass but might be flagged for review
    assert score < 0.85  # Not auto-blocked


@pytest.mark.asyncio
async def test_moderation_analyze_text():
    """Test full analyze_text response."""
    client = PerspectiveAPIClient()

    result = await client.analyze_text("Hello there!")

    assert "scores" in result
    assert "max_score" in result
    assert "flagged_attributes" in result
    assert "action" in result
    assert result["action"] in ["pass", "review", "block"]


# ===== Message Event Handling Tests =====


@pytest.mark.asyncio
async def test_handle_message_event_success(
    test_user: User, test_user2: User, async_db_session: AsyncSession
):
    """Test handling a valid message event."""
    from_user_id = test_user.id
    data = {"to_user_id": str(test_user2.id), "content": "Hello, this is a test message!"}

    # Execute handler
    await handle_message_event(from_user_id, data, async_db_session)

    # Verify message was created
    from sqlalchemy import select

    result = await async_db_session.execute(
        select(Message).where(
            Message.from_user_id == from_user_id, Message.to_user_id == test_user2.id
        )
    )
    message = result.scalar_one_or_none()

    assert message is not None
    assert message.content == "Hello, this is a test message!"
    assert message.from_user_id == from_user_id
    assert message.to_user_id == test_user2.id
    assert message.read_at is None


@pytest.mark.asyncio
async def test_handle_message_event_blocked_content(
    test_user: User, test_user2: User, async_db_session: AsyncSession
):
    """Test that toxic content is blocked."""
    from_user_id = test_user.id
    data = {
        "to_user_id": str(test_user2.id),
        "content": "I hate you stupid idiot die fuck shit",
    }

    # Execute handler
    await handle_message_event(from_user_id, data, async_db_session)

    # Verify message was NOT created
    from sqlalchemy import select

    result = await async_db_session.execute(
        select(Message).where(
            Message.from_user_id == from_user_id, Message.to_user_id == test_user2.id
        )
    )
    message = result.scalar_one_or_none()

    # Message should be blocked
    assert message is None


# ===== Typing Indicator Tests =====


@pytest.mark.asyncio
async def test_typing_indicator_sent(connection_manager: ConnectionManager):
    """Test sending typing indicator."""
    from_user_id = uuid4()
    to_user_id = uuid4()

    # Mock WebSocket connection for recipient
    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send_json(self, data):
            self.messages.append(data)

    mock_ws = MockWebSocket()
    connection_manager.active_connections[to_user_id] = mock_ws

    # Send typing indicator
    await connection_manager.handle_typing_indicator(from_user_id, to_user_id, True)

    # Verify message was sent
    assert len(mock_ws.messages) == 1
    message = mock_ws.messages[0]
    assert message["type"] == "typing"
    assert message["data"]["user_id"] == str(from_user_id)
    assert message["data"]["is_typing"] is True


# ===== Read Receipt Tests =====


@pytest.mark.asyncio
async def test_read_receipt_sent(connection_manager: ConnectionManager):
    """Test sending read receipt."""
    message_id = uuid4()
    reader_id = uuid4()
    sender_id = uuid4()

    # Mock WebSocket for sender
    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send_json(self, data):
            self.messages.append(data)

    mock_ws = MockWebSocket()
    connection_manager.active_connections[sender_id] = mock_ws

    # Send read receipt
    await connection_manager.handle_read_receipt(message_id, reader_id, sender_id)

    # Verify message was sent
    assert len(mock_ws.messages) == 1
    message = mock_ws.messages[0]
    assert message["type"] == "read"
    assert message["data"]["message_id"] == str(message_id)
    assert message["data"]["read_by"] == str(reader_id)
    assert "read_at" in message["data"]


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_send_message_to_online_user(connection_manager: ConnectionManager):
    """Test sending message to an online user."""
    user_id = uuid4()

    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send_json(self, data):
            self.messages.append(data)

    mock_ws = MockWebSocket()
    connection_manager.active_connections[user_id] = mock_ws

    from services.messaging.schemas import WebSocketMessage

    test_message = WebSocketMessage(type="test", data={"content": "Test message"})

    # Send message
    result = await connection_manager.send_message_to_user(user_id, test_message)

    assert result is True
    assert len(mock_ws.messages) == 1
    assert mock_ws.messages[0]["type"] == "test"


@pytest.mark.asyncio
async def test_send_message_to_offline_user(connection_manager: ConnectionManager):
    """Test sending message to an offline user."""
    user_id = uuid4()

    from services.messaging.schemas import WebSocketMessage

    test_message = WebSocketMessage(type="test", data={"content": "Test message"})

    # Send message
    result = await connection_manager.send_message_to_user(user_id, test_message)

    # Should return False since user not connected
    assert result is False


@pytest.mark.asyncio
async def test_broadcast_to_multiple_users(connection_manager: ConnectionManager):
    """Test broadcasting message to multiple users."""
    user1_id = uuid4()
    user2_id = uuid4()

    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def send_json(self, data):
            self.messages.append(data)

    mock_ws1 = MockWebSocket()
    mock_ws2 = MockWebSocket()
    connection_manager.active_connections[user1_id] = mock_ws1
    connection_manager.active_connections[user2_id] = mock_ws2

    from services.messaging.schemas import WebSocketMessage

    test_message = WebSocketMessage(type="broadcast", data={"announcement": "System message"})

    # Broadcast to both users
    await connection_manager.broadcast_to_users([user1_id, user2_id], test_message)

    # Verify both received the message
    assert len(mock_ws1.messages) == 1
    assert len(mock_ws2.messages) == 1
    assert mock_ws1.messages[0]["type"] == "broadcast"
    assert mock_ws2.messages[0]["type"] == "broadcast"
