"""
Reporting services — KPI computation for the dashboard and TresorIA.

Cahier des charges §12.1:
- ~15 KPIs pré-calculés
- Injectés dans le prompt du LLM pour TresorIA
- Jamais de SQL direct généré par le LLM
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from django.db.models import Sum, Count, Q
from finance.models import Payment, Invoice, Expense, Account, Channel, PaymentStatus, InvoiceStatus
from finance.services.forecast import forecast_cashflow


def compute_kpis() -> dict[str, Any]:
    """
    Compute ~15 KPIs for the dashboard and TresorIA chatbot.

    Returns a dict with all KPIs needed by the frontend.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # ── Soldes par canal ──────────────────────────────────────────────
    solde_par_canal = {}
    for channel_code, _label in Channel.choices:
        total = Payment.objects.filter(
            channel=channel_code, paid_at__lte=now
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        solde_par_canal[channel_code] = float(total)

    solde_total = sum(solde_par_canal.values())

    # ── Encaissements / décaissements 7j & 30j ───────────────────────
    encaisse_7j = Payment.objects.filter(
        paid_at__gte=seven_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    encaisse_30j = Payment.objects.filter(
        paid_at__gte=thirty_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    decaisse_7j = Expense.objects.filter(
        paid_at__gte=seven_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    decaisse_30j = Expense.objects.filter(
        paid_at__gte=thirty_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    # ── Factures ─────────────────────────────────────────────────────
    factures_en_attente = Invoice.objects.filter(status=InvoiceStatus.EN_ATTENTE).count()
    factures_en_retard = Invoice.objects.filter(
        status=InvoiceStatus.EN_ATTENTE,
        due_date__lt=now.date(),
    ).count()

    # ── Paiements ────────────────────────────────────────────────────
    paiements_a_valider = Payment.objects.filter(status=PaymentStatus.A_VALIDER).count()
    nb_anomalies = Payment.objects.filter(status=PaymentStatus.ANOMALIE).count()

    # ── Top 5 clients (par montant payé) ──────────────────────────────
    top_clients = (
        Payment.objects.exclude(payer_name="")
        .values("payer_name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")[:5]
    )
    top_clients_list = [
        {"name": c["payer_name"], "total": float(c["total"]), "count": c["count"]}
        for c in top_clients
    ]

    # ── Prévisions Holt-Winters ──────────────────────────────────────
    # Use cached forecast if available, else compute on-the-fly
    from finance.models import ForecastCache
    try:
        cached_30 = ForecastCache.objects.get(days=30)
        prevision_j30 = sum(cached_30.forecast_data) if cached_30.forecast_data else 0.0
    except ForecastCache.DoesNotExist:
        # Compute on-the-fly (slower)
        f30 = forecast_cashflow(days=30)
        prevision_j30 = f30.get("cumulative_forecast", 0.0)

    try:
        cached_7 = ForecastCache.objects.get(days=7)
        prevision_j7 = sum(cached_7.forecast_data) if cached_7.forecast_data else 0.0
    except ForecastCache.DoesNotExist:
        f7 = forecast_cashflow(days=7)
        prevision_j7 = f7.get("cumulative_forecast", 0.0)

    return {
        # Soldes
        "solde_total": solde_total,
        "solde_par_canal": solde_par_canal,
        # Flux
        "encaisse_7j": float(encaisse_7j),
        "encaisse_30j": float(encaisse_30j),
        "decaisse_7j": float(decaisse_7j),
        "decaisse_30j": float(decaisse_30j),
        "flux_net_7j": float(encaisse_7j) - float(decaisse_7j),
        "flux_net_30j": float(encaisse_30j) - float(decaisse_30j),
        # Factures
        "factures_en_attente": factures_en_attente,
        "factures_en_retard": factures_en_retard,
        # Paiements
        "paiements_a_valider": paiements_a_valider,
        "nb_anomalies": nb_anomalies,
        # Prévisions
        "prevision_j7": prevision_j7,
        "prevision_j30": prevision_j30,
        # Top clients
        "top_5_clients": top_clients_list,
    }
