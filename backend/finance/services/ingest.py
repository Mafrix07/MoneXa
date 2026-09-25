"""Ingestion idempotente : NormalizedTransaction → Payment (ledger)."""
from __future__ import annotations

from django.db import transaction

from finance.connectors.base import NormalizedTransaction
from finance.models import Payment, PaymentStatus
from finance.services.anomalies import detect_anomalies
from finance.services.matcher import match_payment


def existing_by_ref(provider_ref: str) -> Payment | None:
    return Payment.objects.filter(provider_ref=provider_ref).first()


def duplicate_response(payment: Payment) -> dict:
    return {
        "detail": "Doublon potentiel : cette référence opérateur existe déjà.",
        "type": "DUPLICATE",
        "category": "doublon_potentiel",
        "label": "Anomalie détectée",
        "provider_ref": payment.provider_ref,
        "existing_payment_id": payment.id,
        "criteria": [
            {"label": "Référence identique", "matched": True},
            {"label": "Montant identique", "matched": True, "value": str(payment.amount)},
            {"label": "Même canal", "matched": True, "value": payment.channel},
        ],
    }


def ingest_normalized(tx: NormalizedTransaction, user, *, apply_match: bool = True) -> tuple[Payment, bool]:
    """
    Crée le paiement si provider_ref inconnu.
    Si déjà connu → IGNORE (idempotence), created=False.
    """
    fields = tx.to_ledger_fields()
    ref = fields["provider_ref"]
    existing = existing_by_ref(ref)
    if existing:
        return existing, False

    with transaction.atomic():
        payment = Payment(
            provider_ref=ref,
            amount=fields["amount"],
            channel=fields["channel"],
            payer_name=fields["payer_name"],
            payer_phone=fields["payer_phone"],
            paid_at=fields["paid_at"],
            raw_text=fields["raw_text"][:4000] if fields["raw_text"] else "",
            created_by=user,
        )
        if tx.direction == "OUT":
            payment.status = PaymentStatus.NON_RATTACHE
        payment.save()
        if apply_match and tx.direction != "OUT":
            new_status, invoice, method = match_payment(payment)
            payment.status = new_status
            payment.match_method = method
            if invoice:
                payment.invoice = invoice
            payment.save()
            detect_anomalies(payment)
    return payment, True
