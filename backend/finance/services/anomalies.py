"""
Détection d'anomalies hybride (cahier des charges §13.2):

1. Règles déterministes (temps réel):
   - Doublon de provider_ref (renvoyé par la contrainte DB UNIQUE)
   - Écart facture / paiement (montant payé != montant facturé)
   - Paiement sans facture (NON_RATTACHE)
   - Paiement hors fenêtre temporelle (date paiement < date facture)
2. Scoring ML (batch) — Isolation Forest sur 90 jours d'historique
   - Paiements atypiques (montant inhabituel, horaire inhabituel, canal inhabituel)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal

from finance.models import Payment, Invoice, PaymentStatus


SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"


def detect_anomalies(payment: Payment) -> List[dict]:
    """
    Run all rule-based anomaly checks on a payment.

    Returns:
        list of dicts: [
            {"severity": "critical", "type": "Doublon provider_ref",
             "description": "...", "payment_id": payment.id},
            ...
        ]
    """
    anomalies: List[dict] = []
    now = datetime.now(timezone.utc)

    # Rule 1 — Écart facture / paiement
    if payment.invoice_id:
        try:
            invoice = payment.invoice
            if invoice.amount != payment.amount:
                ecart = abs(invoice.amount - payment.amount)
                anomalies.append({
                    "severity": SEVERITY_WARNING,
                    "type": "Écart facture / paiement",
                    "description": (
                        f"{invoice.reference} — facturé {invoice.amount:,.2f} FCFA, "
                        f"payé {payment.amount:,.2f} FCFA (écart {ecart:,.2f})"
                    ),
                    "payment_id": payment.id,
                })
        except Invoice.DoesNotExist:
            pass

    # Rule 2 — Paiement sans facture (NON_RATTACHE)
    if payment.status == PaymentStatus.NON_RATTACHE or not payment.invoice_id:
        if not payment.invoice_id:
            anomalies.append({
                "severity": SEVERITY_WARNING,
                "type": "Paiement sans facture",
                "description": (
                    f"{payment.provider_ref} — paiement non rattaché à une facture"
                ),
                "payment_id": payment.id,
            })

    # Rule 3 — Paiement hors fenêtre temporelle (avant la facture)
    if payment.invoice_id:
        try:
            invoice = payment.invoice
            if payment.paid_at.date() < invoice.issue_date:
                anomalies.append({
                    "severity": SEVERITY_CRITICAL,
                    "type": "Paiement hors fenêtre temporelle",
                    "description": (
                        f"{payment.provider_ref} — paiement le "
                        f"{payment.paid_at:%Y-%m-%d} antérieur à la facture "
                        f"{invoice.reference} émise le {invoice.issue_date:%Y-%m-%d}"
                    ),
                    "payment_id": payment.id,
                })
        except Invoice.DoesNotExist:
            pass

    # Rule 4 — Paiement nocturne (heuristique: entre 22h et 06h = suspect)
    hour_local = payment.paid_at.hour
    if 22 <= hour_local or hour_local < 6:
        anomalies.append({
            "severity": SEVERITY_INFO,
            "type": "Paiement nocturne",
            "description": (
                f"{payment.provider_ref} — paiement effectué à "
                f"{payment.paid_at:%H:%M} (heures non habituelles)"
            ),
            "payment_id": payment.id,
        })

    return anomalies


def score_isolation_forest(organization=None) -> List[dict]:
    """
    Batch ML scoring — Isolation Forest on 90 days of payments.

    Returns:
        list of {payment_id, score, flagged} for payments with score > 0.7.
    """
    from sklearn.ensemble import IsolationForest
    import numpy as np

    qs = Payment.objects.all()
    if organization is not None:
        qs = qs.filter(organization=organization)
    payments = list(qs.order_by("-paid_at")[:500])
    if len(payments) < 30:
        # Not enough data for ML
        return []

    # Features: amount (log), hour_of_day, channel_encoded
    X = []
    channel_map = {"TMONEY": 0, "MOOV": 1, "FLOOZ": 1, "BANQUE": 2, "ESPECES": 3}
    for p in payments:
        amount_log = float(np.log1p(float(p.amount)))
        hour = p.paid_at.hour
        channel_enc = channel_map.get(p.channel, 0)
        X.append([amount_log, hour, channel_enc])

    X_arr = np.array(X)
    clf = IsolationForest(contamination=0.05, random_state=42)
    clf.fit(X_arr)
    # decision_function: higher = more normal; negate so higher = more anomalous
    raw_scores = -clf.decision_function(X_arr)
    # Normalize to [0, 1]
    min_s, max_s = raw_scores.min(), raw_scores.max()
    if max_s > min_s:
        normalized = (raw_scores - min_s) / (max_s - min_s)
    else:
        normalized = raw_scores * 0

    flagged = []
    for p, score in zip(payments, normalized):
        if score > 0.7:
            flagged.append({
                "payment_id": p.id,
                "provider_ref": p.provider_ref,
                "score": float(score),
                "flagged": True,
            })

    return flagged
