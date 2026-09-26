"""API jeton caisse — ingest facture + paiement via matcher existant."""
import pytest
from django.urls import reverse
from django.utils import timezone as dj_timezone
from rest_framework.test import APIClient

from finance.models import Channel, Invoice, Payment, PaymentStatus, PosCredential
from finance.services.pos import generate_pos_secret


@pytest.mark.django_db
def test_pos_invoice_and_payment_match_mxa(gerant):
    raw, digest, hint = generate_pos_secret()
    PosCredential.objects.create(
        organization=gerant.organization,
        name="Caisse test",
        channel=Channel.ESPECES,
        token_hash=digest,
        token_hint=hint,
        created_by=gerant,
    )
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    inv = api.post(
        "/api/pos/v1/invoices/",
        {
            "client_name": "Snack Avenue",
            "amount": "15000.00",
            "ticket_id": "POS-42",
        },
        format="json",
    )
    assert inv.status_code == 201, inv.content
    mxa = inv.json()["monexa_ref"]
    assert mxa.startswith("MXA-")
    again = api.post(
        "/api/pos/v1/invoices/",
        {"client_name": "Snack Avenue", "amount": "15000.00", "ticket_id": "POS-42"},
        format="json",
    )
    assert again.status_code == 200
    assert again.json()["created"] is False

    pay = api.post(
        "/api/pos/v1/payments/",
        {
            "provider_ref": "POSPAY-42",
            "amount": "15000.00",
            "channel": "ESPECES",
            "payer_name": "Snack Avenue",
            "monexa_ref": mxa,
        },
        format="json",
    )
    assert pay.status_code == 201, pay.content
    payment = Payment.objects.get(provider_ref="POSPAY-42")
    assert payment.organization_id == gerant.organization_id
    assert payment.status in {PaymentStatus.RECONCILIE, PaymentStatus.A_VALIDER}
    invoice = Invoice.objects.get(pos_ticket_id="POS-42")
    assert invoice.monexa_ref == mxa


@pytest.mark.django_db
def test_pos_rejects_revoked_and_bad_token(gerant):
    raw, digest, hint = generate_pos_secret()
    cred = PosCredential.objects.create(
        organization=gerant.organization,
        name="Caisse",
        token_hash=digest,
        token_hint=hint,
        created_by=gerant,
    )
    cred.revoked_at = dj_timezone.now()
    cred.save(update_fields=["revoked_at"])
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    resp = api.get("/api/pos/v1/ping/")
    assert resp.status_code == 401
    api.credentials(HTTP_AUTHORIZATION="Bearer mxpos_live_nope")
    resp2 = api.get("/api/pos/v1/ping/")
    assert resp2.status_code == 401


@pytest.mark.django_db
def test_gerant_can_create_pos_token_on_sources(client, gerant):
    client.force_login(gerant)
    resp = client.post(reverse("website:pos_token_create"), {"name": "Tiroir", "channel": "ESPECES"})
    assert resp.status_code == 302
    assert PosCredential.objects.filter(organization=gerant.organization, name="Tiroir").exists()
    page = client.get(reverse("website:sources"))
    assert page.status_code == 200
    assert "Copiez ce jeton maintenant".encode() in page.content
    gone = client.get(reverse("website:sources"))
    assert "Copiez ce jeton maintenant".encode() not in gone.content
