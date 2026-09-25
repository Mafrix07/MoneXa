"""Parcours Golden Demo bout-en-bout."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone as dj_timezone

from finance.models import Invoice, Payment, PaymentStatus


GOLDEN_SMS = (
    "Moov Money: credit 50000 FCFA de ABC Services "
    "ID MV849321 le 25/09/2026 09:15"
)


@pytest.mark.django_db
def test_golden_demo_sms_match_then_duplicate(caissier_client, caissier):
    call_command("seed_golden_demo")
    inv = Invoice.objects.get(reference="FACT-2026-0001")
    assert inv.amount == Decimal("50000")

    resp = caissier_client.post(
        "/api/evidence/",
        {"kind": "sms", "text": GOLDEN_SMS},
        format="json",
    )
    assert resp.status_code == 201
    payment = resp.data["payment"]
    assert payment["provider_ref"] == "MV849321"
    assert payment["status"] in (PaymentStatus.RECONCILIE, "RECONCILIE")
    assert resp.data["explain"]["criteria"]
    assert any(c["key"] == "amount" and c["matched"] for c in resp.data["explain"]["criteria"])

    dup = caissier_client.post(
        "/api/evidence/",
        {"kind": "sms", "text": GOLDEN_SMS},
        format="json",
    )
    assert dup.status_code == 409
    assert dup.data["type"] == "DUPLICATE"
    assert Payment.objects.filter(provider_ref="MV849321").count() == 1

    dash = caissier_client.get("/api/dashboard/summary/")
    assert dash.status_code == 200
    assert dash.data["solde_par_canal"]["MOOV"] >= 50000

    ask = caissier_client.post(
        "/api/assistant/ask/",
        {"question": "Quelle est ma situation de tresorerie et quelles anomalies dois-je verifier ?"},
        format="json",
    )
    assert ask.status_code == 200
    assert "FCFA" in ask.data["answer"] or "trésorerie" in ask.data["answer"].lower() or "anomal" in ask.data["answer"].lower()


@pytest.mark.django_db
def test_sms_invalid_evidence(caissier_client):
    resp = caissier_client.post(
        "/api/evidence/",
        {"kind": "sms", "text": "bonjour ceci n'est pas un recu"},
        format="json",
    )
    assert resp.status_code in (400, 422)


@pytest.mark.django_db
def test_sources_rbac(caissier_client, gerant_client):
    assert caissier_client.get("/api/sources/").status_code == 403
    listed = gerant_client.get("/api/sources/")
    assert listed.status_code == 200
