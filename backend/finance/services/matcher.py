"""
Cascade de réconciliation — MXA d'abord, jamais de RECONCILIE auto sans MXA.

1. AUTO_MXA     : MXA-XXXXXX connue + montant = facture → RECONCILIE
                  MXA inconnue ou montant ≠ → ANOMALIE
2. AUTO_REF     : FACT-* dans la preuve + montant = → A_VALIDER (humain)
                  montant ≠ → ANOMALIE
3. AUTO_MONTANT : montant + fenêtre 7 jours → A_VALIDER (jamais auto)
4. FUZZY        : nom/téléphone > 0.8 → A_VALIDER
5. NON_RATTACHE : aucune correspondance
"""
from __future__ import annotations

import re
from datetime import timedelta
from difflib import SequenceMatcher
from typing import Optional, Tuple

from finance.models import (
    Invoice, InvoiceStatus, MatchMethod, Payment, PaymentStatus,
)

_MXA_RE = re.compile(r"\b(MXA-[A-HJ-NP-Z2-9]{6})\b", re.IGNORECASE)


def extract_mxa_ref(text: str) -> Optional[str]:
    if not text:
        return None
    match = _MXA_RE.search(text)
    return match.group(1).upper() if match else None


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _haystack(payment: Payment) -> str:
    return f"{payment.provider_ref or ''} {payment.raw_text or ''}"


def _open_invoices(payment: Payment):
    qs = Invoice.objects.filter(status__in=Invoice.OPEN_STATUSES)
    if payment.organization_id:
        qs = qs.filter(organization_id=payment.organization_id)
    return qs


def _org_invoices(payment: Payment):
    qs = Invoice.objects.all()
    if payment.organization_id:
        qs = qs.filter(organization_id=payment.organization_id)
    return qs


def _find_by_reference(payment: Payment) -> Optional[Invoice]:
    hay = _haystack(payment)
    for invoice in _open_invoices(payment):
        if invoice.reference and invoice.reference in hay:
            return invoice
    return None


def _find_by_amount_and_date(payment: Payment) -> Optional[Invoice]:
    candidates = _open_invoices(payment).filter(
        amount=payment.amount,
        issue_date__lte=payment.paid_at.date(),
        issue_date__gte=payment.paid_at.date() - timedelta(days=7),
    )
    return candidates.first()


def _find_by_fuzzy_payer(payment: Payment) -> Optional[Invoice]:
    threshold = 0.8
    best_match: Optional[Invoice] = None
    best_score: float = 0.0
    for invoice in _open_invoices(payment):
        score = max(
            _similarity(payment.payer_name, invoice.client_name),
            _similarity(payment.payer_phone, invoice.client_phone),
        )
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
    mxa = extract_mxa_ref(_haystack(payment))
    if mxa:
        invoice = _org_invoices(payment).filter(monexa_ref__iexact=mxa).first()
        if invoice is None:
            return PaymentStatus.ANOMALIE, None, MatchMethod.AUTO_MXA
        counted = invoice.amount_paid()
        if (
            payment.pk
            and payment.invoice_id == invoice.id
            and payment.status == PaymentStatus.RECONCILIE
        ):
            counted -= payment.amount
        remaining = invoice.amount - counted
        if remaining < 0:
            remaining = invoice.amount
        if payment.amount > remaining:
            return PaymentStatus.ANOMALIE, invoice, MatchMethod.AUTO_MXA
        if invoice.status in Invoice.CLOSED_STATUSES:
            return PaymentStatus.ANOMALIE, invoice, MatchMethod.AUTO_MXA
        return PaymentStatus.RECONCILIE, invoice, MatchMethod.AUTO_MXA

    invoice = _find_by_reference(payment)
    if invoice:
        if invoice.amount != payment.amount:
            return PaymentStatus.ANOMALIE, invoice, MatchMethod.AUTO_REF
        return PaymentStatus.A_VALIDER, invoice, MatchMethod.AUTO_REF

    invoice = _find_by_amount_and_date(payment)
    if invoice:
        return PaymentStatus.A_VALIDER, invoice, MatchMethod.AUTO_MONTANT

    invoice = _find_by_fuzzy_payer(payment)
    if invoice:
        return PaymentStatus.A_VALIDER, invoice, MatchMethod.FUZZY

    return PaymentStatus.NON_RATTACHE, None, MatchMethod.MANUEL


def apply_match_to_payment(payment: Payment, *, user=None) -> Payment:
    """Écrit le match, recalcule la facture, journalise auto-rapprochement / anomalie."""
    from auditing.services import log_action
    from finance.services.anomalies import detect_anomalies

    old_status = payment.status
    status, invoice, method = match_payment(payment)
    payment.status = status
    payment.match_method = method
    payment.invoice = invoice
    payment.save()
    if invoice:
        invoice.recompute_from_payments()

    actor = user or payment.created_by
    details = {
        "old_status": old_status,
        "new_status": status,
        "method": method,
        "invoice": invoice.reference if invoice else None,
        "monexa_ref": invoice.monexa_ref if invoice else None,
        "provider_ref": payment.provider_ref,
    }
    if status == PaymentStatus.RECONCILIE and method == MatchMethod.AUTO_MXA:
        log_action(
            user=actor,
            action="RAPPROCHEMENT_AUTOMATIQUE",
            entity="Payment",
            entity_id=payment.id,
            details=details,
        )
    elif status == PaymentStatus.ANOMALIE:
        log_action(
            user=actor,
            action="ANOMALIE_CREEE",
            entity="Payment",
            entity_id=payment.id,
            details=details,
        )

    for anomaly in detect_anomalies(payment):
        if anomaly.get("severity") in ("warning", "critical") and status != PaymentStatus.ANOMALIE:
            log_action(
                user=actor,
                action="ANOMALIE_CREEE",
                entity="Payment",
                entity_id=payment.id,
                details=anomaly,
            )
    return payment


def _criteria_for(payment: Payment, invoice: Optional[Invoice]) -> list[dict]:
    mxa = extract_mxa_ref(_haystack(payment))
    criteria = [
        {
            "key": "mxa",
            "label": "Référence MONEXA (MXA-XXXXXX)",
            "matched": bool(invoice and mxa and invoice.monexa_ref.upper() == mxa),
            "value": mxa or "Absente",
        },
    ]
    if invoice is None:
        criteria.append(
            {"key": "invoice", "label": "Facture candidate", "matched": False, "value": "Aucune"},
        )
        if mxa:
            criteria[0]["value"] = f"{mxa} (inconnue)"
        return criteria
    ref_in = bool(invoice.reference and invoice.reference in _haystack(payment))
    amount_ok = invoice.amount == payment.amount
    name_ok = _name_score(payment, invoice) >= 0.8
    date_ok = _date_compatible(payment, invoice)
    criteria.extend([
        {
            "key": "reference",
            "label": "Référence facture",
            "matched": ref_in,
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
    ])
    return criteria


def _confidence_from_criteria(criteria: list[dict], method: str, status: str) -> float:
    weights = {"mxa": 0.45, "reference": 0.20, "amount": 0.25, "date": 0.15, "counterparty": 0.15}
    score = 0.0
    total = 0.0
    for item in criteria:
        key = item.get("key")
        if key not in weights:
            continue
        total += weights[key]
        if item.get("matched"):
            score += weights[key]
    ratio = (score / total) if total else 0.0
    if method == MatchMethod.AUTO_MXA and status == PaymentStatus.RECONCILIE:
        return 0.97
    if method == MatchMethod.AUTO_MXA:
        return 0.20
    if method == MatchMethod.AUTO_MONTANT and status == PaymentStatus.A_VALIDER:
        by_key = {c["key"]: c.get("matched") for c in criteria}
        if by_key.get("amount") and by_key.get("date") and by_key.get("counterparty"):
            return 0.92
        return round(min(max(ratio, 0.55), 0.85), 2)
    if method == MatchMethod.AUTO_REF and status == PaymentStatus.A_VALIDER:
        return round(min(max(ratio, 0.70), 0.88), 2)
    if method == MatchMethod.FUZZY:
        return round(min(max(ratio, 0.40), 0.75), 2)
    if status == PaymentStatus.NON_RATTACHE:
        return min(ratio, 0.25)
    return round(float(ratio), 2)


def explain_payment(payment: Payment) -> dict:
    invoice = payment.invoice
    if invoice is None:
        status, invoice, method = match_payment(payment)
    else:
        status, method = payment.status, payment.match_method

    criteria = _criteria_for(payment, invoice)
    confidence = _confidence_from_criteria(criteria, method, payment.status)
    if confidence >= 0.95 and payment.status == PaymentStatus.RECONCILIE:
        level, label = "HIGH", "Rapprochement automatique (MXA)"
    elif payment.status == PaymentStatus.A_VALIDER:
        level, label = "MEDIUM", "À valider (intervention humaine)"
    else:
        level, label = "LOW", "Non rapproché ou anomalie"

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
                "monexa_ref": invoice.monexa_ref,
                "client_name": invoice.client_name,
                "amount": str(invoice.amount),
                "status": invoice.status,
                "amount_paid": str(invoice.amount_paid()),
                "amount_due": str(invoice.amount_due()),
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
