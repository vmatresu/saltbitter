"""
Comprehensive tests for messaging service REST API endpoints.

Tests cover:
- Getting conversation list
- Getting message history with pagination
- Reporting users/messages
- Blocking and unblocking users
- Error handling and validation
"""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base, Message, User
from services.auth.security import create_access_token, hash_password
from services.messaging.models import BlockedUser, MessageReport

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_test"
)


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


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
def test_user3(db_session: Session) -> User:
    """Create a third test user."""
    user = User(
        email="user3@example.com",
        password_hash=hash_password("TestPassword123"),
        verified=True,
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def access_token(test_user: User) -> str:
    """Create an access token for test_user."""
    return create_access_token(str(test_user.id))


@pytest.fixture
def test_client(db_session: Session):
    """Create a test client with database session override."""
    from main import app
    from database.connection import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ===== Message History Tests =====


def test_get_conversations_empty(test_client: TestClient, test_user: User, access_token: str):
    """Test getting conversations when no messages exist."""
    response = test_client.get(
        "/api/messages/", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_conversations_with_messages(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    test_user3: User,
    access_token: str,
    db_session: Session,
):
    """Test getting conversations with multiple users."""
    # Create messages
    msg1 = Message(
        from_user_id=test_user.id, to_user_id=test_user2.id, content="Hello user2!"
    )
    msg2 = Message(
        from_user_id=test_user2.id, to_user_id=test_user.id, content="Hi back!"
    )
    msg3 = Message(
        from_user_id=test_user.id, to_user_id=test_user3.id, content="Hey user3"
    )

    db_session.add_all([msg1, msg2, msg3])
    db_session.commit()

    response = test_client.get(
        "/api/messages/", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Two conversation partners

    # Check that conversations include both users
    user_ids = [conv["user_id"] for conv in data]
    assert str(test_user2.id) in user_ids
    assert str(test_user3.id) in user_ids


def test_get_message_history_pagination(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    access_token: str,
    db_session: Session,
):
    """Test paginated message history."""
    # Create 60 messages
    for i in range(60):
        msg = Message(
            from_user_id=test_user.id if i % 2 == 0 else test_user2.id,
            to_user_id=test_user2.id if i % 2 == 0 else test_user.id,
            content=f"Message {i}",
        )
        db_session.add(msg)
    db_session.commit()

    # Get first page
    response = test_client.get(
        f"/api/messages/{test_user2.id}?page=1&page_size=50",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 50
    assert data["total"] == 60
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert data["has_more"] is True

    # Get second page
    response = test_client.get(
        f"/api/messages/{test_user2.id}?page=2&page_size=50",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 10
    assert data["has_more"] is False


def test_get_message_history_blocked_user(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    access_token: str,
    db_session: Session,
):
    """Test that message history is blocked when users have blocked each other."""
    # Block user2
    block = BlockedUser(blocker_user_id=test_user.id, blocked_user_id=test_user2.id)
    db_session.add(block)
    db_session.commit()

    response = test_client.get(
        f"/api/messages/{test_user2.id}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 403
    assert "blocked" in response.json()["detail"].lower()


# ===== Report Tests =====


def test_report_user_success(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    access_token: str,
    db_session: Session,
):
    """Test successfully reporting a user."""
    report_data = {"reason": "Inappropriate behavior in messages", "message_id": None}

    response = test_client.post(
        f"/api/messages/{test_user2.id}/report",
        json=report_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "report_id" in data
    assert "submitted successfully" in data["message"]

    # Verify report in database
    reports = db_session.query(MessageReport).all()
    assert len(reports) == 1
    assert reports[0].reporter_user_id == test_user.id
    assert reports[0].reported_user_id == test_user2.id
    assert reports[0].status == "pending"


def test_report_with_message_id(
    test_client: TestClient,
    test_user: User,
    test_user2: User,
    access_token: str,
    db_session: Session,
):
    """Test reporting a specific message."""
    # Create a message
    msg = Message(from_user_id=test_user2.id, to_user_id=test_user.id, content="Bad content")
    db_session.add(msg)
    db_session.commit()

    report_data = {
        "reason": "Inappropriate content in this specific message",
        "message_id": str(msg.id),
    }

    response = test_client.post(
        f"/api/messages/{test_user2.id}/report",
        json=report_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201

    # Verify message_id is stored
    report = db_session.query(MessageReport).first()
    assert report.message_id == msg.id


# ===== Block/Unblock Tests =====


def test_block_user_success(
    test_client: TestClient, test_user: User, test_user2: User, access_token: str, db_session: Session
):
    """Test successfully blocking a user."""
    response = test_client.post(
        f"/api/messages/blocks/{test_user2.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "blocked successfully" in data["message"]

    # Verify block in database
    blocks = db_session.query(BlockedUser).all()
    assert len(blocks) == 1
    assert blocks[0].blocker_user_id == test_user.id
    assert blocks[0].blocked_user_id == test_user2.id


def test_block_user_already_blocked(
    test_client: TestClient, test_user: User, test_user2: User, access_token: str, db_session: Session
):
    """Test blocking a user that's already blocked."""
    # Block user first
    block = BlockedUser(blocker_user_id=test_user.id, blocked_user_id=test_user2.id)
    db_session.add(block)
    db_session.commit()

    response = test_client.post(
        f"/api/messages/blocks/{test_user2.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert "already blocked" in response.json()["detail"].lower()


def test_unblock_user_success(
    test_client: TestClient, test_user: User, test_user2: User, access_token: str, db_session: Session
):
    """Test successfully unblocking a user."""
    # Block user first
    block = BlockedUser(blocker_user_id=test_user.id, blocked_user_id=test_user2.id)
    db_session.add(block)
    db_session.commit()

    response = test_client.delete(
        f"/api/messages/blocks/{test_user2.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "unblocked successfully" in data["message"]

    # Verify block removed from database
    blocks = db_session.query(BlockedUser).all()
    assert len(blocks) == 0


def test_unblock_user_not_blocked(
    test_client: TestClient, test_user: User, test_user2: User, access_token: str
):
    """Test unblocking a user that's not blocked."""
    response = test_client.delete(
        f"/api/messages/blocks/{test_user2.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ===== Authorization Tests =====


def test_get_messages_without_auth(test_client: TestClient):
    """Test accessing messages without authentication."""
    response = test_client.get("/api/messages/")
    assert response.status_code in [401, 403]


def test_report_without_auth(test_client: TestClient):
    """Test reporting without authentication."""
    report_data = {"reason": "Test reason", "message_id": None}
    response = test_client.post(f"/api/messages/{uuid4()}/report", json=report_data)
    assert response.status_code in [401, 403]


def test_block_without_auth(test_client: TestClient):
    """Test blocking without authentication."""
    response = test_client.post(f"/api/messages/blocks/{uuid4()}")
    assert response.status_code in [401, 403]
