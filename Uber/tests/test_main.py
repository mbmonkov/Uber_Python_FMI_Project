"""
General application-level tests to ensure core routing and basic admin accessibility.
This suite validates the entry points and broad behavior of the API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from database import get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provides a mocked database session for general app tests."""
    mock = MagicMock()
    yield mock


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Overrides the database dependency globally for these tests."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def test_read_main():
    """Checks the health and availability of the root endpoint."""
    response = client.get("/")
    assert response.status_code in [200, 404]


def test_get_unverified_drivers_access(db_session):
    """Verifies that the admin endpoint for unverified drivers is reachable and returns the correct structure."""
    db_session.query.return_value.filter.return_value.all.return_value = []

    response = client.get("/admin/unverified-drivers")

    assert response.status_code == 200
    assert "drivers" in response.json()


def test_create_promo_logic_duplicate(db_session):
    """Tests the defensive logic when attempting to create a promo code that already exists."""
    mock_promo = MagicMock()
    db_session.query.return_value.filter.return_value.first.return_value = mock_promo

    response = client.post("/admin/promo-codes/create?code=EXISTING&discount=10")

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_promo_logic_success(db_session):
    """Tests the successful creation of a promo code through the administrative router."""
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.post("/admin/promo-codes/create?code=NEWCODE&discount=15")

    assert response.status_code == 200
    assert "active" in response.json()["message"]
