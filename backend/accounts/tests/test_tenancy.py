"""Isolation multi-tenant — un utilisateur ne voit jamais l'autre organisation."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, Role, User
from finance.models import Channel, Invoice, InvoiceStatus, Payment, PaymentStatus


def _org(name, slug):
    return Organization.objects.create(name=name, slug=slug, country="TG", currency="XOF")


def _user(email, role, org):
    return User.objects.create_user(
        email=email, password="Testpass123!", role=role, organization=org,
    )


def _invoice(user, ref, org):
    return Invoice.objects.create(
        organization=org,
        reference=ref,
        client_name="Client A" if org.slug == "org-a" else "Client B",
        amount=Decimal("10000"),
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=7),
        status=InvoiceStatus.EN_ATTENTE,
        created_by=user,
    )


def _payment(user, ref, org):
    return Payment.objects.create(
        organization=org,
        provider_ref=ref,
        amount=Decimal("10000"),
        channel=Channel.MOOV,
        payer_name="Payeur",
        paid_at=timezone.now(),
        status=PaymentStatus.NON_RATTACHE,
        created_by=user,
    )


@pytest.mark.django_db
def test_cross_tenant_payment_list_and_direct_id():
    org_a = _org("Entreprise A", "org-a")
    org_b = _org("Entreprise B", "org-b")
    gerant_a = _user("a@test.tg", Role.GERANT, org_a)
    gerant_b = _user("b@test.tg", Role.GERANT, org_b)
    pay_a = _payment(gerant_a, "MV-A-1", org_a)
    pay_b = _payment(gerant_b, "MV-B-1", org_b)

    client = APIClient()
    client.force_authenticate(user=gerant_a)
    listed = client.get("/api/payments/")
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.data["results"]}
    assert pay_a.id in ids
    assert pay_b.id not in ids

    detail_b = client.get(f"/api/payments/{pay_b.id}/")
    assert detail_b.status_code == 404

    summary = client.get("/api/dashboard/summary/")
    assert summary.status_code == 200
    # solde total ne doit pas inclure B
    export = client.get("/api/reports/export/", {"export_format": "csv", "model": "payments"})
    assert export.status_code == 200
    body = export.content.decode("utf-8")
    assert "MV-A-1" in body
    assert "MV-B-1" not in body


@pytest.mark.django_db
def test_cross_tenant_invoice_isolation():
    org_a = _org("Entreprise A", "org-a")
    org_b = _org("Entreprise B", "org-b")
    gerant_a = _user("a2@test.tg", Role.GERANT, org_a)
    gerant_b = _user("b2@test.tg", Role.GERANT, org_b)
    inv_a = _invoice(gerant_a, "FACT-2026-9001", org_a)
    inv_b = _invoice(gerant_b, "FACT-2026-9001", org_b)

    client = APIClient()
    client.force_authenticate(user=gerant_a)
    listed = client.get("/api/invoices/")
    ids = {row["id"] for row in listed.data["results"]}
    assert inv_a.id in ids
    assert inv_b.id not in ids
    assert client.get(f"/api/invoices/{inv_b.id}/").status_code == 404


@pytest.mark.django_db
def test_register_creates_organization_and_gerant():
    client = APIClient()
    res = client.post(
        "/api/auth/register/",
        {
            "email": "fondateur@demo.tg",
            "password": "Testpass123!",
            "password2": "Testpass123!",
            "organization_name": "PME Nord",
            "sector": "Négoce",
            "country": "TG",
            "currency": "XOF",
        },
        format="json",
    )
    assert res.status_code == 201
    assert res.data["user"]["role"] == "GERANT"
    assert res.data["organization"]["name"] == "PME Nord"
    assert res.data["access"]
    user = User.objects.get(email="fondateur@demo.tg")
    assert user.organization_id == res.data["organization"]["id"]
