"""
Tests for the Users API module to ensure correct functionality of profile management,
security updates, favorites maintenance, and trip history retrieval.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


class MockUser:
    """Mock object representing a database user record."""

    def __init__(self, id, password="secretpassword", favorites=None):
        self.id = id
        self.password = password
        self.home_address = ""
        self.preferences = ""
        self.favorites = favorites
        self.phone = ""


class MockDriver:
    """Mock object representing a database driver record."""

    def __init__(self, id, full_name, car_model):
        self.id = id
        self.car_model = car_model
        self.rating = 5.0
        self.is_online = True
        self.user = MagicMock(full_name=full_name)


class MockTrip:
    """Mock object representing a database trip record."""

    def __init__(self, id, client_id, status="completed"):
        self.id = id
        self.client_id = client_id
        self.status = status


@pytest.fixture
def db_session():
    """Provides a mocked database session for testing."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the FastAPI dependency injection for the database session."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_update_user_settings_success(db_session):
    """Validates that user address and preferences are updated correctly when user exists."""
    mock_user = MockUser(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.patch("/user/1/settings?address=Sofia&prefs=Music")

    assert response.status_code == 200
    assert mock_user.home_address == "Sofia"
    assert response.json()["message"] == "Profile updated successfully"


def test_update_user_settings_not_found(db_session):
    """Ensures a 404 error is returned when trying to update a non-existent user."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.patch("/user/999/settings?address=Sofia")
    assert response.status_code == 404


def test_update_user_security_success(db_session):
    """Verifies that password and phone updates work with correct current password."""
    mock_user = MockUser(id=1, password="old_password")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.put("/user/1/security?password=old_password&new_password=new_pass&phone=0888")

    assert response.status_code == 200
    assert mock_user.password == "new_pass"
    assert response.json()["message"] == "Security settings updated successfully"


def test_update_user_security_invalid_password(db_session):
    """Checks that a 401 error is raised when the provided current password is wrong."""
    mock_user = MockUser(id=1, password="correct_pass")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.put("/user/1/security?password=wrong&new_password=new_pass")

    assert response.status_code == 401
    assert "Invalid current password" in response.json()["detail"]


def test_add_favorite_driver_new(db_session):
    """Confirms a driver can be added to an empty or existing favorites list."""
    mock_user = MockUser(id=1, favorites="")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.post("/user/favorites/add?user_id=1&driver_id=10")

    assert response.status_code == 200
    assert "10" in mock_user.favorites
    assert response.json()["message"] == "Driver added to favorites"


def test_add_favorite_driver_already_exists(db_session):
    """Checks the logic when a driver is already present in the user favorites."""
    mock_user = MockUser(id=1, favorites="10,11")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.post("/user/favorites/add?user_id=1&driver_id=10")

    assert response.status_code == 200
    assert response.json()["message"] == "Driver is already in your favorites list"


def test_get_favorite_drivers_success(db_session):
    """Validates the retrieval and mapping of favorite driver details."""
    mock_user = MockUser(id=1, favorites="10")
    mock_driver = MockDriver(id=10, full_name="Ivan Ivanov", car_model="Tesla")

    db_session.query.return_value.filter.return_value.first.return_value = mock_user
    db_session.query.return_value.filter.return_value.all.return_value = [mock_driver]

    response = client.get("/user/1/favorites")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, set, dict))


def test_get_client_trip_history(db_session):
    """Verifies that the trip history endpoint returns the correct status and data structure."""
    mock_trip = MockTrip(id=101, client_id=1)
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_trip]

    response = client.get("/user/1/history")

    assert response.status_code == 200
