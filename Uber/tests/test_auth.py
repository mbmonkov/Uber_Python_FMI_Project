"""
Unit tests for the Authentication API module.
Covers user registration uniqueness constraints and multi-step login validation logic.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


class MockUser:
    """Mock object representing a user record in the database."""

    def __init__(self, id, full_name, email, password, role="client.html", is_active=True):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.phone = "0888111222"
        self.password = password
        self.role = role
        self.is_active = is_active


@pytest.fixture
def db_session():
    """Provides a mocked SQLAlchemy session for authentication tests."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency to use the mock session for all tests."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_register_user_success(db_session):
    """Verifies that a new user is correctly added to the database when credentials are unique."""
    db_session.query.return_value.filter.return_value.first.return_value = None
    db_session.refresh.side_effect = lambda x: setattr(x, 'id', 1)

    payload = {
        "full_name": "New User",
        "email": "new@test.com",
        "phone": "0888000000",
        "password": "securepassword",
        "role": "client.html"
    }

    response = client.post("/register", json=payload)

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["full_name"] == "New User"
    assert db_session.add.called


def test_register_user_already_exists(db_session):
    """Ensures a 400 error is raised if the email or phone number is already in use."""
    mock_user = MockUser(1, "Existing", "old@test.com", "pass")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    payload = {
        "full_name": "Duplicate",
        "email": "old@test.com",
        "phone": "0888111222",
        "password": "pass",
        "role": "client.html"
    }

    response = client.post("/register", json=payload)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(db_session):
    """Validates successful authentication when valid credentials are provided."""
    mock_user = MockUser(10, "Logged User", "user@test.com", "secret")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.post("/login?email=user@test.com&password=secret")

    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["role"] == "client.html"


def test_login_invalid_credentials(db_session):
    """Checks that a 401 error is returned for non-existent users or incorrect passwords."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.post("/login?email=wrong@test.com&password=wrong")

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_blocked_user(db_session):
    """Ensures that users with inactive accounts are blocked from logging in with a 403 error."""
    mock_user = MockUser(11, "Blocked User", "blocked@test.com", "pass", is_active=False)
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.post("/login?email=blocked@test.com&password=pass")

    assert response.status_code == 403
    assert "Account is blocked" in response.json()["detail"]
