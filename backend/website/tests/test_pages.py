import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_is_public(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"une seule v" in resp.content or "une seule".encode() in resp.content


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    resp = client.get(reverse("website:dashboard"))
    assert resp.status_code == 302
    assert "/connexion/" in resp.url
