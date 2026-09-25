"""
Tests RBAC — vérifient que chaque rôle n'a accès qu'à son périmètre.
"""
import pytest
from accounts.models import Role


@pytest.mark.django_db
def test_gerant_role_helpers(gerant):
    assert gerant.is_gerant() is True
    assert gerant.is_comptable_or_higher() is True
    assert gerant.is_caissier_or_higher() is True


@pytest.mark.django_db
def test_comptable_role_helpers(comptable):
    assert comptable.is_gerant() is False
    assert comptable.is_comptable_or_higher() is True
    assert comptable.is_caissier_or_higher() is True


@pytest.mark.django_db
def test_caissier_role_helpers(caissier):
    assert caissier.is_gerant() is False
    assert caissier.is_comptable_or_higher() is False
    assert caissier.is_caissier_or_higher() is True


@pytest.mark.django_db
def test_caissier_cannot_access_audit_logs(caissier_client):
    """Le caissier n'a pas accès au journal d'audit."""
    resp = caissier_client.get("/api/audit-logs/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_comptable_cannot_access_audit_logs(comptable_client):
    """Le comptable n'a pas accès au journal d'audit (réservé Gérant)."""
    resp = comptable_client.get("/api/audit-logs/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_gerant_can_access_audit_logs(gerant_client):
    """Le gérant a accès au journal d'audit."""
    resp = gerant_client.get("/api/audit-logs/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_unauthenticated_cannot_access_dashboard(api_client):
    """Un utilisateur non authentifié ne peut pas accéder au dashboard."""
    resp = api_client.get("/api/dashboard/summary/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_2fa_toggle_restricted_to_gerant(comptable_client):
    """Seul le gérant peut activer le 2FA."""
    resp = comptable_client.patch("/api/auth/me/2fa/", {})
    assert resp.status_code == 403


@pytest.mark.django_db
def test_gerant_can_toggle_2fa(gerant_client, gerant):
    """Le gérant peut activer/désactiver son 2FA."""
    initial = gerant.is_2fa_enabled
    resp = gerant_client.patch("/api/auth/me/2fa/", {})
    assert resp.status_code == 200
    gerant.refresh_from_db()
    assert gerant.is_2fa_enabled != initial


@pytest.mark.django_db
def test_user_email_is_unique(db):
    """L'email doit être unique (rule Username_FIELD=email)."""
    User = pytest.importorskip("accounts.models").User
    User.objects.create_user(
        email="dup@test.tg", password="Testpass123!",
        role=Role.CAISSIER,
    )
    with pytest.raises(Exception):
        User.objects.create_user(
            email="dup@test.tg", password="Testpass123!",
            role=Role.GERANT,
        )
