"""
Unit tests for the Administrative API module.
Covers system statistics, driver verification, user blocking, review moderation, and promo code management.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db
import models

client = TestClient(app)


class MockAdminUser:
    """Mock object representing a user for administrative actions."""

    def __init__(self, id, full_name="Admin", role="admin"):
        self.id = id
        self.full_name = full_name
        self.role = role
        self.is_verified = False
        self.is_active = True


class MockPromoCode:
    """Mock object representing a promotional code."""

    def __init__(self, code, discount):
        self.code = code
        self.discount_percentage = discount
        self.is_active = True


@pytest.fixture
def db_session():
    """Provides a mocked SQLAlchemy session for admin tests."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency for the duration of the module tests."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_get_system_stats(db_session):
    """Verifies that system metrics are correctly aggregated and returned."""
    db_session.query.return_value.count.side_effect = [100, 10, 50]
    db_session.query.return_value.filter.return_value.scalar.return_value = 1500.50

    response = client.get("/admin/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 100
    assert data["total_incomes_bgn"] == 1500.5


def test_get_unverified_drivers(db_session):
    """Tests the retrieval of a list containing drivers awaiting account verification."""
    mock_driver = MockAdminUser(id=5, full_name="Pending Driver")
    db_session.query.return_value.filter.return_value.all.return_value = [mock_driver]

    response = client.get("/admin/unverified-drivers")

    assert response.status_code == 200
    assert len(response.json()["drivers"]) == 1
    assert response.json()["drivers"][0]["full_name"] == "Pending Driver"


def test_verify_driver_success(db_session):
    """Validates that a driver can be successfully verified by an administrator."""
    mock_user = MockAdminUser(id=5, full_name="John Doe")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.patch("/admin/verify-driver/5")

    assert response.status_code == 200
    assert mock_user.is_verified is True
    assert "is verified" in response.json()["message"]


def test_block_user_success(db_session):
    """Confirms that an administrator can block a user's access to the platform."""
    mock_user = MockAdminUser(id=10, full_name="Bad User")
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    response = client.patch("/admin/users/10/block")

    assert response.status_code == 200
    assert mock_user.is_active is False


def test_get_all_reviews(db_session):
    """Verifies that all system reviews can be retrieved for moderation purposes."""
    mock_review = MagicMock()
    mock_review.id = 1
    mock_review.driver.user.full_name = "Driver Name"
    db_session.query.return_value.all.return_value = [mock_review]

    response = client.get("/admin/reviews/all")

    assert response.status_code == 200
    assert "all reviews" in response.json()


def test_delete_review_success(db_session):
    """Validates the successful removal of a review from the system."""
    mock_review = MagicMock()
    db_session.query.return_value.filter.return_value.first.return_value = mock_review

    response = client.delete("/admin/reviews/1")

    assert response.status_code == 200
    assert db_session.delete.called


def test_create_promo_code_success(db_session):
    """Tests the successful creation of a new active promotional code."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.post("/admin/promo-codes/create?code=SUMMER20&discount=20")

    assert response.status_code == 200
    assert "SUMMER20" in response.json()["message"]
    assert db_session.add.called


def test_delete_promo_code_success(db_session):
    """Confirms that a promotional code can be permanently removed from the system."""
    mock_promo = MockPromoCode("WINTER10", 10)
    db_session.query.return_value.filter.return_value.first.return_value = mock_promo

    response = client.delete("/admin/promo-codes/WINTER10")

    assert response.status_code == 200
    assert db_session.delete.called


def test_get_all_promo_codes_success(db_session):
    """
    Tests retrieval of active promo codes.
    Fixed KeyError by using spec and proper attribute mapping.
    """
    mock_promo = MagicMock(spec=models.PromoCode)
    mock_promo.code = "SAVE20"
    mock_promo.is_active = True
    mock_promo.discount_percentage = 10
    mock_promo.__dict__ = {
        "code": "SAVE20",
        "is_active": True,
        "discount_percentage": 10
    }

    db_session.query.return_value.filter.return_value.all.return_value = [mock_promo]

    response = client.get("/admin/promo-codes/active")

    assert response.status_code == 200

    data = response.json()
    assert "promo codes" in data
    assert data["promo codes"][0]["code"] == "SAVE20"
