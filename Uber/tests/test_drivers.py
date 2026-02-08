"""
Unit tests for the Drivers API module.
Covers profile setup, service management, shift status toggling, earnings, and performance metrics.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


class MockUser:
    """Mock object for a database user record during driver setup."""

    def __init__(self, id, role="driver"):
        self.id = id
        self.role = role


class MockDriver:
    """Mock object for a database driver record including vehicle and status details."""

    def __init__(self, id, user_id=1):
        self.id = id
        self.user_id = user_id
        self.car_model = "BMW"
        self.license_plate = "TX1234CB"
        self.is_online = False
        self.total_earnings = 500.55
        self.price_per_km = 1.50
        self.schedule = "Mon-Fri"
        self.current_location = "Sofia City"


class MockReview:
    """Mock object for a database review record."""

    def __init__(self):
        self.client_name = "Alice"
        self.rating = 5
        self.comment = "Great driver!"


@pytest.fixture
def db_session():
    """Provides a mocked SQLAlchemy session for driver operations."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for the duration of the module tests."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_setup_driver_success(db_session):
    """Verifies that a driver profile is successfully created for a user with the driver role."""
    mock_user = MockUser(id=1, role="driver")
    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_user),
        MagicMock(first=lambda: None)
    ]
    db_session.refresh.side_effect = lambda x: setattr(x, 'id', 10)

    response = client.post("/driver/setup?user_id=1&car_model=BMW&license_plate=TX1234CB")

    assert response.status_code == 200
    assert response.json()["driver_id"] == 10
    assert "ready for use" in response.json()["message"]


def test_setup_driver_wrong_role(db_session):
    """Ensures a 400 error is returned when a user without the driver role tries to set up a profile."""
    mock_user = MockUser(id=2, role="client.html")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.post("/driver/setup?user_id=2&car_model=Tesla&license_plate=B1234")

    assert response.status_code == 400
    assert "permission" in response.json()["detail"]


def test_manage_service_success(db_session):
    """Validates that service parameters like price and location are updated correctly."""
    mock_driver = MockDriver(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = mock_driver

    response = client.put("/driver/1/manage-service?price=2.5&location=Center")

    assert response.status_code == 200
    assert mock_driver.price_per_km == 2.5
    assert mock_driver.current_location == "Center"


def test_update_status_toggle(db_session):
    """Checks that the shift status toggles correctly between online and offline."""
    mock_driver = MockDriver(id=1)
    mock_driver.is_online = False
    db_session.query.return_value.filter.return_value.first.return_value = mock_driver

    response = client.patch("/driver/1/shift")

    assert response.status_code == 200
    assert mock_driver.is_online is True


def test_get_driver_earnings_success(db_session):
    """
    Verifies that the earnings and completed trips count are retrieved accurately
    for an existing driver and that the balance is correctly rounded.
    """
    mock_driver = MagicMock()
    mock_driver.total_earnings = 500.55

    db_session.query.return_value.filter.return_value.first.return_value = mock_driver
    db_session.query.return_value.filter.return_value.count.return_value = 5

    response = client.get("/driver/1/earnings")

    assert response.status_code == 200
    assert response.json()["balance"] == 500.55
    assert response.json()["trips_count"] == 5


def test_get_driver_earnings_not_found(db_session):
    """
    Ensures that the API returns a 404 Not Found status code and a descriptive
    error message when the driver ID does not exist in the database.
    """
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/driver/999/earnings")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_location_success(db_session):
    """Validates the geographic location update for an existing driver."""
    mock_driver = MockDriver(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = mock_driver

    response = client.patch("/driver/1/location?new_location=Airport")

    assert response.status_code == 200
    assert mock_driver.current_location == "Airport"


def test_get_driver_trip_history(db_session):
    """Ensures that the chronological trip history is returned for a driver."""
    mock_trip = MagicMock()
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_trip]

    response = client.get("/driver/1/trips/history")

    assert response.status_code == 200
    assert "trips" in response.json()


def test_get_driver_reviews_success(db_session):
    """Validates the retrieval of customer reviews and ratings for a driver."""
    mock_driver = MockDriver(id=1)
    mock_review = MockReview()

    db_session.query.return_value.filter.side_effect = [
        MagicMock(first=lambda: mock_driver),
        MagicMock(all=lambda: [mock_review])
    ]

    response = client.get("/driver/1/reviews")

    assert response.status_code == 200
    assert response.json()["total_reviews"] == 1
    assert response.json()["reviews"][0]["client_name"] == "Alice"
