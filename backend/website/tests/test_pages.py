import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_is_public(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"une seule v" in resp.content or "une seule".encode() in resp.content
    assert b"scenes/m2.jpeg" in resp.content
    assert b"scenes/m5.jpeg" in resp.content


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


@pytest.mark.django_db
def test_payment_detail_loads_after_org_audit_filter(client, gerant):
    from decimal import Decimal
    from django.utils import timezone as dj_timezone
    from finance.models import Channel, Payment

    payment = Payment.objects.create(
        organization=gerant.organization,
        provider_ref="TX-DETAIL-1",
        amount=Decimal("15000"),
        channel=Channel.TMONEY,
        payer_name="Snack Avenue de la Paix",
        paid_at=dj_timezone.now(),
        created_by=gerant,
    )
    client.force_login(gerant)
    resp = client.get(reverse("website:payment_detail", args=[payment.pk]))
    assert resp.status_code == 200
    assert b"TX-DETAIL-1" in resp.content
