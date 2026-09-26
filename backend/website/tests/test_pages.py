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
        "invoice_create",
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


@pytest.mark.django_db
def test_caissier_creates_and_loads_invoice(client, gerant):
    from decimal import Decimal
    from django.utils import timezone as dj_timezone
    from datetime import timedelta

    client.force_login(gerant)
    today = dj_timezone.now().date()
    resp = client.post(
        reverse("website:invoice_create"),
        {
            "client_name": "Snack Avenue",
            "client_phone": "+22890000000",
            "amount": "25000",
            "issue_date": today.isoformat(),
            "due_date": (today + timedelta(days=7)).isoformat(),
        },
    )
    assert resp.status_code == 302
    listed = client.get(reverse("website:invoices") + "?q=Snack")
    assert listed.status_code == 200
    assert b"Snack Avenue" in listed.content
    assert b"FACT-" in listed.content
    assert b"MXA-" in listed.content
    from finance.models import Invoice
    inv = Invoice.objects.get(client_name="Snack Avenue")
    detail = client.get(reverse("website:invoice_detail", args=[inv.pk]))
    assert detail.status_code == 200
    assert inv.monexa_ref.encode() in detail.content


@pytest.mark.django_db
def test_duplicate_extraction_flash_is_danger(client, gerant):
    from decimal import Decimal
    from django.utils import timezone as dj_timezone
    from finance.models import Channel, Payment

    sms = "Moov Money: credit 50000 FCFA de ABC Services ID MV849321 le 25/09/2026 09:15"
    Payment.objects.create(
        organization=gerant.organization,
        provider_ref="MV849321",
        amount=Decimal("50000"),
        channel=Channel.MOOV,
        payer_name="ABC Services",
        paid_at=dj_timezone.now(),
        created_by=gerant,
    )
    client.force_login(gerant)
    resp = client.post(
        reverse("website:evidence"),
        {"text": sms, "confirm": "1"},
        follow=True,
    )
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Doublon potentiel" in body
    assert "mx-flash--danger" in body
