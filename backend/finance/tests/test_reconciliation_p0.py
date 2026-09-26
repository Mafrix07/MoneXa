"""P0 réconciliation : MXA, cascade, statuts facture, RBAC, audit."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone as dj_timezone

from auditing.models import AuditLog
from finance.models import (
    Channel, Invoice, InvoiceStatus, MatchMethod, Payment, PaymentStatus,
)
from finance.services.ai_pipeline import extract_payment_from_text
from finance.services.anomalies import detect_anomalies
from finance.services.matcher import apply_match_to_payment, match_payment
from finance.services.sms_parser import parse_sms_text

GOLDEN_SMS = (
    "T-Money: Vous avez recu 50000 FCFA de ABC SARL. "
    "Référence : MXA-8F42K7 ID TX8F42K700 le 25/09/2026 09:15"
)


@pytest.fixture
def invoice_abc(comptable):
    return Invoice.objects.create(
        organization=comptable.organization,
        reference="FACT-2026-00842",
        monexa_ref="MXA-8F42K7",
        client_name="ABC SARL",
        client_phone="+228 92 00 11 22",
        amount=Decimal("50000"),
        issue_date=dj_timezone.now().date() - timedelta(days=1),
        due_date=dj_timezone.now().date() + timedelta(days=14),
        status=InvoiceStatus.EMISE,
        created_by=comptable,
    )


def _pay(user, **kwargs):
    defaults = {
        "organization": user.organization,
        "channel": Channel.TMONEY,
        "payer_name": "ABC SARL",
        "paid_at": dj_timezone.now(),
        "created_by": user,
    }
    defaults.update(kwargs)
    return Payment.objects.create(**defaults)


@pytest.mark.django_db
def test_01_sms_extracts_mxa():
    parsed = parse_sms_text(GOLDEN_SMS)
    assert parsed["monexa_ref"] == "MXA-8F42K7"
    assert parsed["montant"] == Decimal("50000")
    extracted = extract_payment_from_text(GOLDEN_SMS)
    assert extracted["reference"] == "TX8F42K700"
    assert "MXA-8F42K7" in extracted["raw_text"]


@pytest.mark.django_db
def test_02_mxa_exact_reconciles_and_pays_invoice(caissier, invoice_abc):
    payment = _pay(
        caissier,
        provider_ref="TX8F42K700",
        amount=Decimal("50000"),
        raw_text=GOLDEN_SMS,
    )
    apply_match_to_payment(payment, user=caissier)
    payment.refresh_from_db()
    invoice_abc.refresh_from_db()
    assert payment.status == PaymentStatus.RECONCILIE
    assert payment.match_method == MatchMethod.AUTO_MXA
    assert payment.invoice_id == invoice_abc.id
    assert invoice_abc.status == InvoiceStatus.PAYEE
    assert invoice_abc.amount_paid() == Decimal("50000")
    assert invoice_abc.amount_due() == Decimal("0.00")


@pytest.mark.django_db
def test_03_unknown_mxa_is_anomaly_without_invoice(caissier):
    payment = _pay(
        caissier,
        provider_ref="TXUNKNOWN",
        amount=Decimal("50000"),
        raw_text="T-Money recu 50000 FCFA Référence : MXA-ZZZZZ2 ID TXUNKNOWN le 25/09/2026",
    )
    apply_match_to_payment(payment, user=caissier)
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.ANOMALIE
    assert payment.invoice_id is None
    assert payment.match_method == MatchMethod.AUTO_MXA


@pytest.mark.django_db
def test_04_mxa_overpay_is_anomaly(caissier, invoice_abc):
    payment = _pay(
        caissier,
        provider_ref="TXMISMATCH",
        amount=Decimal("80000"),
        raw_text="T-Money recu 80000 FCFA Référence : MXA-8F42K7 ID TXMISMATCH le 25/09/2026",
    )
    apply_match_to_payment(payment, user=caissier)
    payment.refresh_from_db()
    invoice_abc.refresh_from_db()
    assert payment.status == PaymentStatus.ANOMALIE
    assert payment.invoice_id == invoice_abc.id
    assert invoice_abc.status != InvoiceStatus.PAYEE
    assert invoice_abc.amount_paid() == Decimal("0.00")


@pytest.mark.django_db
def test_05_amount_name_date_never_auto_reconcile(caissier, invoice_abc):
    payment = _pay(
        caissier,
        provider_ref="TXNOMXA",
        amount=Decimal("50000"),
        raw_text="T-Money recu 50000 FCFA de ABC SARL ID TXNOMXA le 25/09/2026",
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert method == MatchMethod.AUTO_MONTANT
    assert inv == invoice_abc


@pytest.mark.django_db
def test_06_fact_in_provider_ref_requires_human(caissier, invoice_abc):
    payment = _pay(
        caissier,
        provider_ref=f"TMX{invoice_abc.reference}99",
        amount=Decimal("50000"),
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert method == MatchMethod.AUTO_REF
    assert inv == invoice_abc


@pytest.mark.django_db
def test_07_partial_then_paid(caissier, comptable):
    inv = Invoice.objects.create(
        organization=comptable.organization,
        reference="FACT-2026-00901",
        monexa_ref="MXA-PARTA2",
        client_name="ABC SARL",
        amount=Decimal("50000"),
        issue_date=dj_timezone.now().date() - timedelta(days=1),
        due_date=dj_timezone.now().date() + timedelta(days=10),
        status=InvoiceStatus.EMISE,
        created_by=comptable,
    )
    first = _pay(
        caissier,
        provider_ref="TXPART1",
        amount=Decimal("20000"),
        raw_text="Référence : MXA-PARTA2 recu 20000 FCFA ID TXPART1 le 25/09/2026",
    )
    apply_match_to_payment(first, user=caissier)
    inv.refresh_from_db()
    assert first.status == PaymentStatus.RECONCILIE
    assert inv.status == InvoiceStatus.PARTIELLEMENT_PAYEE
    assert inv.amount_due() == Decimal("30000")

    second = _pay(
        caissier,
        provider_ref="TXPART2",
        amount=Decimal("30000"),
        raw_text="Référence : MXA-PARTA2 recu 30000 FCFA ID TXPART2 le 25/09/2026",
    )
    apply_match_to_payment(second, user=caissier)
    inv.refresh_from_db()
    assert second.status == PaymentStatus.RECONCILIE
    assert inv.status == InvoiceStatus.PAYEE
    assert inv.amount_due() == Decimal("0.00")


@pytest.mark.django_db
def test_08_overpayment_marks_invoice_anomaly(caissier, comptable):
    inv = Invoice.objects.create(
        organization=comptable.organization,
        reference="FACT-2026-00910",
        monexa_ref="MXA-XVERA2",
        client_name="ABC SARL",
        amount=Decimal("30000"),
        issue_date=dj_timezone.now().date() - timedelta(days=1),
        due_date=dj_timezone.now().date() + timedelta(days=10),
        status=InvoiceStatus.EMISE,
        created_by=comptable,
    )
    p1 = _pay(caissier, provider_ref="TXO1", amount=Decimal("30000"), raw_text="Référence : MXA-XVERA2 30000 FCFA ID TXO1")
    apply_match_to_payment(p1, user=caissier)
    inv.amount = Decimal("10000")
    inv.save(update_fields=["amount", "updated_at"])
    inv.recompute_from_payments()
    inv.refresh_from_db()
    assert inv.is_overpaid()
    assert inv.status == InvoiceStatus.ANOMALIE


@pytest.mark.django_db
def test_09_duplicate_operator_ref_and_near_duplicate(caissier_client, caissier, invoice_abc):
    resp = caissier_client.post("/api/evidence/", {"kind": "sms", "text": GOLDEN_SMS}, format="json")
    assert resp.status_code == 201
    dup = caissier_client.post("/api/evidence/", {"kind": "sms", "text": GOLDEN_SMS}, format="json")
    assert dup.status_code == 409
    original = Payment.objects.get(provider_ref="TX8F42K700")
    other = _pay(
        caissier,
        provider_ref="TXNEAR",
        amount=Decimal("50000"),
        channel=Channel.TMONEY,
        paid_at=original.paid_at,
    )
    flags = detect_anomalies(other)
    types = {f["type"] for f in flags}
    assert "Paiement potentiellement dupliqué" in types


@pytest.mark.django_db
def test_10_caissier_cannot_create_invoice(caissier_client):
    resp = caissier_client.post(
        "/api/invoices/",
        {
            "client_name": "Interdit",
            "amount": "1000",
            "issue_date": str(dj_timezone.now().date()),
            "due_date": str((dj_timezone.now() + timedelta(days=7)).date()),
        },
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_11_audit_on_auto_match_and_invoice_refs(comptable_client, caissier, invoice_abc):
    created = comptable_client.post(
        "/api/invoices/",
        {
            "client_name": "Client Audit",
            "amount": "15000",
            "issue_date": str(dj_timezone.now().date()),
            "due_date": str((dj_timezone.now() + timedelta(days=7)).date()),
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.data["monexa_ref"].startswith("MXA-")
    assert AuditLog.objects.filter(action="REFERENCE_GENEREE").exists()

    payment = _pay(
        caissier,
        provider_ref="TXAUDITMXA",
        amount=Decimal("50000"),
        raw_text=GOLDEN_SMS,
    )
    apply_match_to_payment(payment, user=caissier)
    assert AuditLog.objects.filter(action="RAPPROCHEMENT_AUTOMATIQUE", entity_id=str(payment.id)).exists() or \
        AuditLog.objects.filter(action="RAPPROCHEMENT_AUTOMATIQUE").exists()
