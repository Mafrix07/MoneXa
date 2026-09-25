"""
Cascade de réconciliation automatique — 4 niveaux (cahier des charges §13.3):

1. AUTO_REF       : provider_ref contient la référence d'une facture (FACT-YYYY-XXXX)
                   → matching automatique, statut RECONCILIE
2. AUTO_MONTANT   : montant correspond à une facture impayée, date de paiement
                   dans la fenêtre de 7 jours après l'émission
                   → matching automatique, statut A_VALIDER (validation comptable)
3. FUZZY          : similarité > 0.8 entre nom du payeur ou téléphone et un client
                   avec facture impayée
                   → matching proposé, statut A_VALIDER
4. NON_RATTACHE   : aucune correspondance
                   → paiement en anomalie, statut NON_RATTACHE
"""
from __future__ import annotations
from datetime import timedelta
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Optional, Tuple

from finance.models import (
    Invoice, InvoiceStatus, MatchMethod, Payment, PaymentStatus,
)


def _similarity(a: str, b: str) -> float:
    """Return a similarity ratio between two strings (0..1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _find_by_reference(payment: Payment) -> Optional[Invoice]:
    """Level 1 — provider_ref contains an invoice reference."""
    candidates = Invoice.objects.filter(status=InvoiceStatus.EN_ATTENTE)
    for invoice in candidates:
        if invoice.reference and invoice.reference in payment.provider_ref:
            return invoice
    return None


def _find_by_amount_and_date(payment: Payment) -> Optional[Invoice]:
    """Level 2 — exact amount match within 7 days after issue_date."""
    window_end = payment.paid_at.date() + timedelta(days=1)
    candidates = Invoice.objects.filter(
        status=InvoiceStatus.EN_ATTENTE,
        amount=payment.amount,
        issue_date__lte=payment.paid_at.date(),
        issue_date__gte=payment.paid_at.date() - timedelta(days=7),
    )
    return candidates.first()


def _find_by_fuzzy_payer(payment: Payment) -> Optional[Invoice]:
    """Level 3 — payer name/phone similarity > 0.8 with an invoice's client."""
    threshold = 0.8
    candidates = Invoice.objects.filter(status=InvoiceStatus.EN_ATTENTE)
    best_match: Optional[Invoice] = None
    best_score: float = 0.0

    for invoice in candidates:
        score_name = _similarity(payment.payer_name, invoice.client_name)
        score_phone = _similarity(payment.payer_phone, invoice.client_phone)
        score = max(score_name, score_phone)
        if score >= threshold and score > best_score:
            best_match = invoice
            best_score = score

    return best_match


def _date_compatible(payment: Payment, invoice: Invoice) -> bool:
    paid = payment.paid_at.date()
    issued = invoice.issue_date
    return issued <= paid <= issued + timedelta(days=7)


def _name_score(payment: Payment, invoice: Invoice) -> float:
    score = max(
        _similarity(payment.payer_name, invoice.client_name),
        _similarity(payment.payer_phone, invoice.client_phone),
    )
    payer = (payment.payer_name or "").lower()
    client = (invoice.client_name or "").lower()
    if client and payer and (client in payer or payer in client):
        score = max(score, 0.95)
    return score


def match_payment(payment: Payment) -> Tuple[PaymentStatus, Optional[Invoice], MatchMethod]:
    """
    Run the 4-level reconciliation cascade.

    Returns:
        (new_status, matched_invoice_or_None, match_method)
    """
    # Level 1 — exact reference
    invoice = _find_by_reference(payment)
    if invoice:
        return PaymentStatus.RECONCILIE, invoice, MatchMethod.AUTO_REF

    # Level 2 — amount + 7 days window
    invoice = _find_by_amount_and_date(payment)
    if invoice:
        # Montant + date + contrepartie très proche → auto (HIGH), sinon file comptable
        if _name_score(payment, invoice) >= 0.9 and _date_compatible(payment, invoice):
            return PaymentStatus.RECONCILIE, invoice, MatchMethod.AUTO_MONTANT
        return PaymentStatus.A_VALIDER, invoice, MatchMethod.AUTO_MONTANT

    # Level 3 — fuzzy payer
    invoice = _find_by_fuzzy_payer(payment)
    if invoice:
        return PaymentStatus.A_VALIDER, invoice, MatchMethod.FUZZY

    # Level 4 — no match
    return PaymentStatus.NON_RATTACHE, None, MatchMethod.MANUEL


def _criteria_for(payment: Payment, invoice: Optional[Invoice]) -> list[dict]:
    if invoice is None:
        return [
            {"key": "invoice", "label": "Facture candidate", "matched": False, "value": "Aucune"},
        ]
    ref_in_provider = bool(invoice.reference and invoice.reference in (payment.provider_ref or ""))
    ref_in_text = bool(invoice.reference and invoice.reference in (payment.raw_text or ""))
    amount_ok = invoice.amount == payment.amount
    name_ok = _name_score(payment, invoice) >= 0.8
    date_ok = _date_compatible(payment, invoice)
    return [
        {
            "key": "reference",
            "label": "Référence correspondante",
            "matched": ref_in_provider or ref_in_text,
            "value": invoice.reference,
        },
        {
            "key": "amount",
            "label": "Montant identique",
            "matched": amount_ok,
            "value": f"{payment.amount} / {invoice.amount} FCFA",
        },
        {
            "key": "counterparty",
            "label": "Client correspondant",
            "matched": name_ok,
            "value": f"{payment.payer_name} ↔ {invoice.client_name}",
        },
        {
            "key": "date",
            "label": "Date compatible (fenêtre 7 jours)",
            "matched": date_ok,
            "value": f"payé {payment.paid_at.date().isoformat()} / émis {invoice.issue_date.isoformat()}",
        },
    ]


def _confidence_from_criteria(criteria: list[dict], method: str, status: str) -> float:
    matched = sum(1 for c in criteria if c.get("matched"))
    total = max(len(criteria), 1)
    score = matched / total
    if method == MatchMethod.AUTO_REF and status == PaymentStatus.RECONCILIE:
        score = max(score, 0.95)
    elif method == MatchMethod.AUTO_MONTANT and status == PaymentStatus.RECONCILIE:
        score = max(score, 0.90)
    elif method == MatchMethod.AUTO_MONTANT:
        score = min(max(score, 0.55), 0.85)
    elif method == MatchMethod.FUZZY:
        score = min(max(score, 0.40), 0.75)
    elif status == PaymentStatus.NON_RATTACHE:
        score = min(score, 0.25)
    return round(float(score), 2)


def explain_payment(payment: Payment) -> dict:
    """Explication réelle du rapprochement — aucun critère inventé."""
    invoice = payment.invoice
    if invoice is None:
        # Recalcule un candidat pour expliquer l'échec, sans l'écrire
        status, invoice, method = match_payment(payment)
    else:
        status, method = payment.status, payment.match_method

    criteria = _criteria_for(payment, invoice)
    confidence = _confidence_from_criteria(criteria, method, payment.status)
    if confidence >= 0.9 and payment.status == PaymentStatus.RECONCILIE:
        level, label = "HIGH", "Rapprochement automatique"
    elif payment.status == PaymentStatus.A_VALIDER:
        level, label = "MEDIUM", "À valider (intervention humaine)"
    else:
        level, label = "LOW", "Non rapproché"

    return {
        "payment_id": payment.id,
        "provider_ref": payment.provider_ref,
        "amount": str(payment.amount),
        "payer_name": payment.payer_name,
        "channel": payment.channel,
        "status": payment.status,
        "match_method": method,
        "confidence": confidence,
        "confidence_level": level,
        "decision_label": label,
        "invoice": (
            {
                "id": invoice.id,
                "reference": invoice.reference,
                "client_name": invoice.client_name,
                "amount": str(invoice.amount),
            }
            if invoice
            else None
        ),
        "criteria": criteria,
        "disclaimer": (
            "Score calculé à partir des critères ci-dessus. "
            "Ce n'est pas une preuve d'authenticité de la capture."
        ),
    }
