"""Pytest fixtures shared across apps."""
import pytest
from accounts.models import User, Role


@pytest.fixture
def gerant(db):
    """Create a GERANT user."""
    u = User.objects.create_user(
        email="gerant@test.tg", password="Testpass123!",
        role=Role.GERANT, phone="+228 90 00 00 01",
    )
    return u


@pytest.fixture
def comptable(db):
    """Create a COMPTABLE user."""
    u = User.objects.create_user(
        email="comptable@test.tg", password="Testpass123!",
        role=Role.COMPTABLE, phone="+228 91 00 00 02",
    )
    return u


@pytest.fixture
def caissier(db):
    """Create a CAISSIER user."""
    u = User.objects.create_user(
        email="caissier@test.tg", password="Testpass123!",
        role=Role.CAISSIER, phone="+228 92 00 00 03",
    )
    return u


@pytest.fixture
def api_client():
    """Unauthenticated DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def gerant_client(gerant):
    """Authenticated as GERANT."""
    from rest_framework.test import APIClient
    c = APIClient()
    c.force_authenticate(user=gerant)
    return c


@pytest.fixture
def comptable_client(comptable):
    """Authenticated as COMPTABLE."""
    from rest_framework.test import APIClient
    c = APIClient()
    c.force_authenticate(user=comptable)
    return c


@pytest.fixture
def caissier_client(caissier):
    """Authenticated as CAISSIER."""
    from rest_framework.test import APIClient
    c = APIClient()
    c.force_authenticate(user=caissier)
    return c
