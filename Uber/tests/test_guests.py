"""
Unit tests for the Guest Access API module.
Validates public profile retrieval, driver rankings sorting, and availability filtering logic.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


class MockDriver:
    """Mock object representing a driver for guest-facing profile tests."""

    def __init__(self, id, full_name="John Doe", rating=4.5, is_online=True):
        self.id = id
        self.car_model = "Skoda Octavia"
        self.car_category = "Standard"
        self.rating = rating
        self.current_location = "42.6977, 23.3219"
        self.price_per_km = 1.20
        self.is_online = is_online
        self.user = MagicMock(full_name=full_name)


@pytest.fixture
def db_session():
    """Provides a mocked database session for guest access testing."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for the duration of the module tests."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_get_driver_public_profile_success(db_session):
    """Verifies that a driver's public profile is correctly retrieved and mapped."""
    mock_driver = MockDriver(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = mock_driver

    response = client.get("/driver/1/profile")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["full_name"] == "John Doe"
    assert data["rating"] == 4.5


def test_get_driver_public_profile_not_found(db_session):
    """Ensures a 404 error is returned when requesting a non-existent driver ID."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/driver/999/profile")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_drivers_rankings_sorting(db_session):
    drivers = [
        MockDriver(id=1, full_name="Low Rated", rating=3.0),
        MockDriver(id=2, full_name="High Rated", rating=5.0)
    ]
    db_session.query.return_value.all.return_value = drivers

    response = client.get("/drivers/rankings")

    assert response.status_code == 200
    data = response.json()

    assert "rankings" in data
    rankings = data["rankings"]
    assert rankings[0]["rating"] == 5.0
    assert rankings[1]["rating"] == 3.0


def test_get_available_drivers_filtering(db_session):
    """Tests the logic that filters out busy drivers and returns only those who are online."""
    busy_trip_ids = [(10,)]
    available_driver = MockDriver(id=1, is_online=True)

    db_session.query.return_value.filter.return_value.all.side_effect = [
        busy_trip_ids,
        [available_driver]
    ]

    response = client.get("/search/drivers")

    assert response.status_code == 200
    data = response.json()
    assert "available drivers" in data
    assert len(data["available drivers"]) == 1
    assert data["available drivers"][0]["id"] == 1


def test_get_available_drivers_empty(db_session):
    """Verifies the response structure when no online drivers match the search criteria."""
    db_session.query.return_value.filter.return_value.all.side_effect = [[], []]

    response = client.get("/search/drivers")

    assert response.status_code == 200
    assert response.json() == {"available drivers": []}
