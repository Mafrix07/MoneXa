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


def compute_kpis(organization=None) -> dict[str, Any]:
    """
    Compute ~15 KPIs for the dashboard and TresorIA chatbot.
    Toujours scopé à l'organisation (source de vérité ledger).
    """
    payments = Payment.objects.all()
    expenses = Expense.objects.all()
    invoices = Invoice.objects.all()
    if organization is not None:
        payments = payments.filter(organization=organization)
        expenses = expenses.filter(organization=organization)
        invoices = invoices.filter(organization=organization)

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # ── Soldes par canal ──────────────────────────────────────────────
    solde_par_canal = {}
    for channel_code, _label in Channel.choices:
        total = payments.filter(
            channel=channel_code, paid_at__lte=now
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        solde_par_canal[channel_code] = float(total)

    solde_total = sum(solde_par_canal.values())

    # ── Encaissements / décaissements 7j & 30j ───────────────────────
    encaisse_7j = payments.filter(
        paid_at__gte=seven_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    encaisse_30j = payments.filter(
        paid_at__gte=thirty_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    decaisse_7j = expenses.filter(
        paid_at__gte=seven_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    decaisse_30j = expenses.filter(
        paid_at__gte=thirty_days_ago
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    # ── Factures ─────────────────────────────────────────────────────
    factures_en_attente = invoices.filter(
        status__in=["EMISE", "EN_ATTENTE", "PARTIELLEMENT_PAYEE", "EN_RETARD"]
    ).count()
    factures_en_retard = invoices.filter(
        status__in=["EMISE", "EN_ATTENTE", "PARTIELLEMENT_PAYEE", "EN_RETARD"],
        due_date__lt=now.date(),
    ).count()

    # ── Paiements ────────────────────────────────────────────────────
    paiements_a_valider = payments.filter(status=PaymentStatus.A_VALIDER).count()
    nb_anomalies = payments.filter(status=PaymentStatus.ANOMALIE).count()
    paiements_non_rattaches = payments.filter(status=PaymentStatus.NON_RATTACHE).count()

    # ── Top 5 clients (par montant payé) ──────────────────────────────
    top_clients = (
        payments.exclude(payer_name="")
        .values("payer_name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")[:5]
    )
    top_clients_list = [
        {"name": c["payer_name"], "total": float(c["total"]), "count": c["count"]}
        for c in top_clients
    ]

    # ── Prévisions Holt-Winters ──────────────────────────────────────
    from finance.models import ForecastCache
    fc = ForecastCache.objects.all()
    if organization is not None:
        fc = fc.filter(organization=organization)
    try:
        cached_30 = fc.get(days=30)
        prevision_j30 = sum(cached_30.forecast_data) if cached_30.forecast_data else 0.0
    except ForecastCache.DoesNotExist:
        f30 = forecast_cashflow(days=30, organization=organization)
        prevision_j30 = f30.get("cumulative_forecast", 0.0)

    try:
        cached_7 = fc.get(days=7)
        prevision_j7 = sum(cached_7.forecast_data) if cached_7.forecast_data else 0.0
    except ForecastCache.DoesNotExist:
        f7 = forecast_cashflow(days=7, organization=organization)
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
        "anomalies_non_resolues": nb_anomalies,
        "paiements_non_rattaches": paiements_non_rattaches,
        # Prévisions
        "prevision_j7": prevision_j7,
        "prevision_j30": prevision_j30,
        # Top clients
        "top_5_clients": top_clients_list,
    }


def explain_forecast(days: int = 30, organization=None) -> dict:
    """Facteurs réellement présents dans les données — aucune cause inventée."""
    from datetime import datetime, timedelta, timezone
    from finance.models import Expense, Invoice, InvoiceStatus

    kpis = compute_kpis(organization)
    now = datetime.now(timezone.utc)
    horizon = now.date() + timedelta(days=days)
    due = Invoice.objects.filter(
        status__in=["EMISE", "EN_ATTENTE", "PARTIELLEMENT_PAYEE", "EN_RETARD"],
        due_date__gte=now.date(),
        due_date__lte=horizon,
    )
    if organization is not None:
        due = due.filter(organization=organization)
    due_total = due.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    recurring = (
        Expense.objects.filter(paid_at__gte=now - timedelta(days=30))
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    if organization is not None:
        recurring = (
            Expense.objects.filter(
                organization=organization,
                paid_at__gte=now - timedelta(days=30),
            )
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
    factors = []
    if kpis["encaisse_30j"]:
        factors.append({
            "key": "inflows",
            "label": "Encaissements 30 jours",
            "value": kpis["encaisse_30j"],
        })
    if kpis["decaisse_30j"]:
        factors.append({
            "key": "outflows",
            "label": "Décaissements 30 jours",
            "value": kpis["decaisse_30j"],
        })
    if due_total:
        factors.append({
            "key": "invoices_due",
            "label": "Factures en attente arrivant à échéance sur l'horizon",
            "value": float(due_total),
            "count": due.count(),
        })
    for row in recurring[:4]:
        factors.append({
            "key": "expense_category",
            "label": f"Sorties récentes — {row['category']}",
            "value": float(row["total"]),
        })
    if kpis["nb_anomalies"]:
        factors.append({
            "key": "anomalies",
            "label": "Paiements en anomalie (non utilisés comme prévision)",
            "value": kpis["nb_anomalies"],
        })
    today = kpis["solde_total"]
    points = {
        "today": today,
        "j7": today + kpis["prevision_j7"],
        "j30": today + kpis["prevision_j30"],
    }
    # J+15 approx from 30-day cumulative * 0.5 if no dedicated cache
    points["j15"] = today + (kpis["prevision_j30"] * 0.5)
    return {
        "points": points,
        "factors": factors,
        "model": "Holt-Winters sur flux nets historiques (voir /api/reports/forecast/)",
        "disclaimer": "Les causes listées sont dérivées des écritures en base, pas d'une inférence libre.",
        "kpis": {
            "encaisse_30j": kpis["encaisse_30j"],
            "decaisse_30j": kpis["decaisse_30j"],
            "flux_net_30j": kpis["flux_net_30j"],
        },
    }
