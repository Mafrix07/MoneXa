"""Réconciliation explicable — critères réels uniquement."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone as dj_timezone

from finance.models import (
    Channel, Invoice, InvoiceStatus, MatchMethod, Payment, PaymentStatus,
)
from finance.services.matcher import explain_payment, match_payment


@pytest.mark.django_db
def test_high_confidence_amount_name_date(caissier):
    inv = Invoice.objects.create(
        reference=Invoice.generate_reference(),
        client_name="ABC Services",
        amount=Decimal("50000"),
        issue_date=dj_timezone.now().date() - timedelta(days=1),
        due_date=dj_timezone.now().date() + timedelta(days=10),
        status=InvoiceStatus.EN_ATTENTE,
        created_by=caissier,
    )
    payment = Payment.objects.create(
        provider_ref="MV849321",
        amount=Decimal("50000"),
        channel=Channel.MOOV,
        payer_name="ABC Services",
        paid_at=dj_timezone.now(),
        created_by=caissier,
    )
    status, matched, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert matched == inv
    assert method == MatchMethod.AUTO_MONTANT
    payment.invoice = matched
    payment.status = status
    payment.match_method = method
    payment.save()
    expl = explain_payment(payment)
    assert expl["confidence_level"] == "MEDIUM"
    assert expl["confidence"] == 0.92
    by_key = {c["key"]: c["matched"] for c in expl["criteria"]}
    assert by_key["amount"] is True
    assert by_key["counterparty"] is True
    assert by_key["date"] is True
    assert by_key["reference"] is False


@pytest.mark.django_db
def test_explain_unmatched_has_no_fake_criteria(caissier):
    payment = Payment.objects.create(
        provider_ref="ZZZ999",
        amount=Decimal("12"),
        channel=Channel.TMONEY,
        payer_name="Inconnu",
        paid_at=dj_timezone.now(),
        created_by=caissier,
    )
    expl = explain_payment(payment)
    assert expl["confidence_level"] == "LOW"
    assert expl["invoice"] is None
