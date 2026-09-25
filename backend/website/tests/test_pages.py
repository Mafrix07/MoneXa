import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_is_public(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"une seule v" in resp.content or "une seule".encode() in resp.content


@pytest.mark.django_db
def test_login_page_is_public(client):
    resp = client.get(reverse("website:login"))
    assert resp.status_code == 200
    assert b"Bienvenue sur MONEXA" in resp.content


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    resp = client.get(reverse("website:dashboard"))
    assert resp.status_code == 302
    assert "/connexion/" in resp.url


@pytest.mark.django_db
def test_app_pages_require_login(client):
    for name in ("payments", "invoices", "treasury", "evidence", "assistant"):
        resp = client.get(reverse(f"website:{name}"))
        assert resp.status_code == 302


@pytest.mark.django_db
def test_gerant_app_pages_200(client, gerant):
    client.force_login(gerant)
    names = [
        "dashboard",
        "treasury",
        "payments",
        "invoices",
        "reconciliation",
        "anomalies",
        "forecast",
        "sources",
        "assistant",
        "evidence",
        "users",
        "audit",
        "about",
        "services",
        "faq",
        "contact",
    ]
    for name in names:
        resp = client.get(reverse(f"website:{name}"))
        assert resp.status_code == 200, name
