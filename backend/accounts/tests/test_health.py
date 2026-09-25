import pytest


@pytest.mark.django_db
def test_health_ok(api_client):
    resp = api_client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.django_db
def test_ready_ok(api_client):
    resp = api_client.get("/ready/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
