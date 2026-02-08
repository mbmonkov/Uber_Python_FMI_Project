"""
Unit tests for the Messages API module.
Covers message transmission, inbox retrieval, and dual-party chat history logic.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


class MockMessage:
    """Mock object for a database message record."""

    def __init__(self, id, sender_id, receiver_id, content):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = "2026-02-04 12:00:00"
        self.sender = MagicMock(full_name="John Doe")


class MockUser:
    """Mock object for a database user record."""

    def __init__(self, id):
        self.id = id
        self.full_name = "Jane Doe"


@pytest.fixture
def db_session():
    """Provides a mocked SQLAlchemy session for message testing."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for the duration of the test module."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_send_message_success(db_session):
    """Verifies that a message is correctly added to the database when content is valid."""
    db_session.refresh.side_effect = lambda x: setattr(x, 'id', 101)

    response = client.post("/messages/send?sender_id=1&receiver_id=2&content=Hello%20there")

    assert response.status_code == 200
    assert response.json()["message_id"] == 101
    assert response.json()["message"] == "Message sent successfully"
    assert db_session.add.called


def test_send_message_empty_content(db_session):
    """Checks that a 400 error is raised when trying to send an empty or whitespace-only message."""
    response = client.post("/messages/send?sender_id=1&receiver_id=2&content=%20%20%20")

    assert response.status_code == 400
    assert "content cannot be empty" in response.json()["detail"]


def test_get_my_messages_user_not_found(db_session):
    """Ensures a 404 error is returned if the recipient user does not exist."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/messages/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_get_my_messages_success(db_session):
    """Validates the retrieval of a user inbox and the mapping of sender details."""
    mock_user = MockUser(id=2)
    mock_msg = MockMessage(id=50, sender_id=1, receiver_id=2, content="Hi")

    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_user),
        MagicMock(order_by=lambda x: MagicMock(all=lambda: [mock_msg]))
    ]

    response = client.get("/messages/2")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["messages"][0]["sender_name"] == "John Doe"


def test_get_chat_history_logic(db_session):
    """Tests the filtering logic for bidirectional chat history between two users."""
    msg1 = MockMessage(id=1, sender_id=1, receiver_id=2, content="Message from 1")
    msg2 = MockMessage(id=2, sender_id=2, receiver_id=1, content="Reply from 2")

    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [msg1, msg2]

    response = client.get("/messages/chat/1/2")

    assert response.status_code == 200
    history = response.json()["chat_history"]
    assert len(history) == 2
    assert history[0]["is_me"] is True
    assert history[1]["is_me"] is False


def test_get_chat_history_empty(db_session):
    """Verifies that an empty history list is returned when no messages exist between users."""
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    response = client.get("/messages/chat/1/2")

    assert response.status_code == 200
    assert response.json()["chat_history"] == []
