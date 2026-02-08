"""
Unit tests for the Reviews API module.
Validates the feedback system, ensuring review-trip consistency and rating updates.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy import func
from main import app
from database import get_db

client = TestClient(app)


class MockTrip:
    """Mock object for a database trip record for testing purposes."""

    def __init__(self, id, status="completed", driver_id=10):
        self.id = id
        self.status = status
        self.driver_id = driver_id
        self.client = MagicMock(full_name="Alice Smith")


class MockDriver:
    """Mock object for a database driver record to test rating synchronization."""

    def __init__(self, id):
        self.id = id
        self.rating = 0.0


@pytest.fixture
def db_session():
    """Provides a mocked database session for dependency injection."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for all tests in this module."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_leave_review_trip_not_found(db_session):
    """Ensures a 404 response is returned if the trip ID does not exist in the database."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.post("/reviews/add?trip_id=999&rating=5&comment=Great")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def test_leave_review_not_completed(db_session):
    """Verifies that reviews are rejected if the trip status is not 'completed'."""
    mock_trip = MockTrip(id=1, status="searching")
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip

    response = client.post("/reviews/add?trip_id=1&rating=5&comment=Too early")

    assert response.status_code == 400
    assert "only rate completed trips" in response.json()["detail"]


def test_leave_review_success_and_id_return(db_session):
    """Validates successful review submission, ID return, and driver rating update."""
    mock_trip = MockTrip(id=2, status="completed", driver_id=10)
    mock_driver = MockDriver(id=10)

    db_session.add.side_effect = lambda x: setattr(x, 'id', 500)

    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_trip),
        MagicMock(scalar=lambda: 4.8),
        MagicMock(first=lambda: mock_driver)
    ]

    response = client.post("/reviews/add?trip_id=2&rating=5&comment=Excellent")

    assert response.status_code == 200
    data = response.json()
    assert data["review_id"] == 500
    assert "Alice Smith" in data["message"]
    assert mock_driver.rating == 4.8


def test_leave_review_rounding_logic(db_session):
    """Ensures that the driver average rating is correctly rounded to one decimal place."""
    mock_trip = MockTrip(id=3, status="completed", driver_id=20)
    mock_driver = MockDriver(id=20)

    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_trip),
        MagicMock(scalar=lambda: 4.666666),
        MagicMock(first=lambda: mock_driver)
    ]

    client.post("/reviews/add?trip_id=3&rating=4&comment=Good")

    assert mock_driver.rating == 4.7


def test_leave_review_missing_avg(db_session):
    """Checks that the system handles cases where no previous ratings exist for a driver."""
    mock_trip = MockTrip(id=4, status="completed")
    mock_driver = MockDriver(id=10)

    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_trip),
        MagicMock(scalar=lambda: None),
        MagicMock(first=lambda: mock_driver)
    ]

    response = client.post("/reviews/add?trip_id=4&rating=5&comment=Nice")
    assert response.status_code == 200
