"""
Unit tests for the Trips API module.
Covers all success paths and every single 'raise' statement for 100% coverage.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provides a mock database session."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for testing."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_accept_trip_driver_not_found_raise(db_session):
    """Tests 404 raise when driver does not exist."""
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = client.patch("/trip/1/accept?driver_id=999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Driver not found."


def test_accept_trip_not_found_raise(db_session):
    """Tests 404 raise when trip does not exist."""
    mock_driver = MagicMock()
    db_session.query.return_value.filter.return_value.first.side_effect = [mock_driver, None]
    response = client.patch("/trip/1/accept?driver_id=1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found."


def test_accept_trip_already_taken_raise(db_session):
    """Tests 400 raise when trip status is not 'searching'."""
    mock_driver = MagicMock()
    mock_trip = MagicMock(status="accepted")
    db_session.query.return_value.filter.return_value.first.side_effect = [mock_driver, mock_trip]
    response = client.patch("/trip/1/accept?driver_id=1")
    assert response.status_code == 400
    assert "already taken or cancelled" in response.json()["detail"]


def test_cancel_trip_not_found_raise(db_session):
    """Tests 404 raise when trip is not found for cancellation."""
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = client.patch("/trip/1/cancel")
    assert response.status_code == 404
    assert response.json()["detail"] == "Request not found"


def test_cancel_trip_invalid_status_raise(db_session):
    """Tests 400 raise when trip is already completed or cancelled."""
    mock_trip = MagicMock(status="completed")
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip
    response = client.patch("/trip/1/cancel")
    assert response.status_code == 400
    assert "Cannot cancel a trip with status" in response.json()["detail"]


def test_complete_trip_not_found_raise(db_session):
    """Tests 404 raise when trip is not found for completion."""
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = client.patch("/trip/1/complete")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def test_complete_trip_already_finished_raise(db_session):
    """Tests 400 raise when trip is already completed."""
    mock_trip = MagicMock(status="completed")
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip
    response = client.patch("/trip/1/complete")
    assert response.status_code == 400
    assert "already been completed" in response.json()["detail"]


def test_complete_trip_no_driver_assigned_raise(db_session):
    """Tests 400 raise when no driver is assigned to the trip."""
    mock_trip = MagicMock(status="accepted", driver=None, final_price=10.0)
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip
    response = client.patch("/trip/1/complete")
    assert response.status_code == 400
    assert "No driver assigned to this trip" in response.json()["detail"]


def test_track_status_not_found_raise(db_session):
    """Tests 404 raise when tracking a non-existent trip."""
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/trip/1/status")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def test_request_trip_success(db_session):
    """Tests successful trip request creation."""
    trip_data = {
        "client_id": 1, "pickup_location": "A", "destination": "B",
        "car_category": "economy", "final_price": 10.0,
        "is_shared": False, "is_urgent": False
    }

    def mock_refresh(obj): obj.id = 1

    db_session.refresh.side_effect = mock_refresh
    response = client.post("/trip/request", json=trip_data)
    assert response.status_code == 200
    assert "trip_id" in response.json()


def test_calculate_price_full_logic(db_session):
    """Tests price calculation with urgency and promo codes."""
    res = client.get("/trip/calculate-price?original_price=10.0&is_urgent=true")
    assert res.json()["final_price"] == 15.0

    mock_promo = MagicMock(discount_percentage=10.0)
    db_session.query.return_value.filter.return_value.first.return_value = mock_promo
    res = client.get("/trip/calculate-price?original_price=100.0&promo_code=SALE")
    assert res.json()["final_price"] == 90.0

    db_session.query.return_value.filter.return_value.first.return_value = None
    res = client.get("/trip/calculate-price?original_price=100.0&promo_code=FAKE")
    assert res.json()["final_price"] == 100.0


def test_complete_trip_with_zero_price(db_session):
    """Tests the 'amount_to_pay = 10.0' default logic."""
    mock_driver = MagicMock(total_earnings=0.0)
    mock_trip = MagicMock(status="accepted", final_price=0.0, driver=mock_driver)
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip
    client.patch("/trip/1/complete")
    assert mock_driver.total_earnings == 10.0


def test_track_status_searching(db_session):
    """Tests status tracking for 'searching' trips."""
    mock_trip = MagicMock(status="searching", driver=None)
    db_session.query.return_value.filter.return_value.first.return_value = mock_trip
    response = client.get("/trip/1/status")
    assert response.json()["status"] == "searching"


def test_get_available_and_shared_trips(db_session):
    """Tests retrieval of available and shared trips."""
    mock_trip = MagicMock(status="searching", is_shared=True)
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_trip]

    res1 = client.get("/trips/available-trips")
    assert len(res1.json()["available trips"]) == 1

    res2 = client.get("/trips/shared/available")
    assert len(res2.json()["shared trips"]) == 1


def test_accept_trip_success(db_session):
    """Tests successfully accepting a trip."""
    mock_driver = MagicMock(id=1)
    mock_trip = MagicMock(id=1, status="searching")
    db_session.query.return_value.filter.return_value.first.side_effect = [mock_driver, mock_trip]
    response = client.patch("/trip/1/accept?driver_id=1")
    assert response.status_code == 200
    assert mock_trip.status == "accepted"
