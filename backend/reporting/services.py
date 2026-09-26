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
from django.db.models.functions import TruncDate
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

    charts = build_dashboard_charts(
        payments=payments,
        expenses=expenses,
        solde_par_canal=solde_par_canal,
        solde_total=solde_total,
        top_clients=top_clients_list,
        now=now,
    )
    pm = max(float(encaisse_7j), float(decaisse_7j), float(encaisse_30j), float(decaisse_30j), 1.0)
    charts["period"] = [
        {"label": "Encaissé 7j", "value": float(encaisse_7j), "pct": round(float(encaisse_7j) / pm * 100, 1), "kind": "in"},
        {"label": "Décaissé 7j", "value": float(decaisse_7j), "pct": round(float(decaisse_7j) / pm * 100, 1), "kind": "out"},
        {"label": "Encaissé 30j", "value": float(encaisse_30j), "pct": round(float(encaisse_30j) / pm * 100, 1), "kind": "in"},
        {"label": "Décaissé 30j", "value": float(decaisse_30j), "pct": round(float(decaisse_30j) / pm * 100, 1), "kind": "out"},
    ]
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
        "charts": charts,
    }


def build_dashboard_charts(
    *,
    payments,
    expenses,
    solde_par_canal: dict,
    solde_total: float,
    top_clients: list,
    now: datetime,
    days: int = 14,
) -> dict[str, Any]:
    """Séries agrégées depuis le ledger. Aucun montant inventé."""
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    in_by_day: dict = defaultdict(float)
    for row in (
        payments.filter(paid_at__gte=start, paid_at__lte=now)
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    ):
        if row["day"]:
            in_by_day[row["day"].isoformat()] = float(row["total"] or 0)

    out_by_day: dict = defaultdict(float)
    for row in (
        expenses.filter(paid_at__gte=start, paid_at__lte=now)
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    ):
        if row["day"]:
            out_by_day[row["day"].isoformat()] = float(row["total"] or 0)

    series = []
    max_flow = 0.0
    for i in range(days):
        d = start.date() + timedelta(days=i)
        key = d.isoformat()
        enc = in_by_day.get(key, 0.0)
        dec = out_by_day.get(key, 0.0)
        max_flow = max(max_flow, enc, dec)
        series.append({"date": key, "label": d.strftime("%d/%m"), "encaisse": enc, "decaisse": dec})
    for point in series:
        point["encaisse_pct"] = round((point["encaisse"] / max_flow) * 100, 1) if max_flow else 0
        point["decaisse_pct"] = round((point["decaisse"] / max_flow) * 100, 1) if max_flow else 0

    channels = []
    for code, label in Channel.choices:
        amount = float(solde_par_canal.get(code, 0) or 0)
        channels.append({
            "code": code,
            "label": label,
            "amount": amount,
            "pct": round((amount / solde_total) * 100, 1) if solde_total else 0,
        })

    status_rows = {
        row["status"]: row["c"]
        for row in payments.values("status").annotate(c=Count("id"))
    }
    status_total = sum(status_rows.values()) or 0
    statuses = []
    for code, label in PaymentStatus.choices:
        count = int(status_rows.get(code, 0) or 0)
        statuses.append({
            "code": code,
            "label": label,
            "count": count,
            "pct": round((count / status_total) * 100, 1) if status_total else 0,
        })

    client_max = max((c["total"] for c in top_clients), default=0) or 0
    clients = [
        {**c, "pct": round((c["total"] / client_max) * 100, 1) if client_max else 0}
        for c in top_clients
    ]

    circ = 226.08
    offset = 0.0
    donut = []
    palette = {
        "TMONEY": "#063082",
        "MOOV": "#0f6b45",
        "BANQUE": "#44546e",
        "ESPECES": "#3d2b1f",
        "FLOOZ": "#b45309",
    }
    for ch in channels:
        if not ch["amount"]:
            continue
        length = (ch["pct"] / 100.0) * circ
        donut.append({
            **ch,
            "color": palette.get(ch["code"], "#063082"),
            "dash": f"{length:.2f} {circ:.2f}",
            "offset": round(-offset, 2),
        })
        offset += length
    if solde_total >= 1_000_000:
        center = f"{solde_total / 1_000_000:.1f} M"
    elif solde_total >= 1_000:
        center = f"{solde_total / 1_000:.0f} k"
    else:
        center = f"{solde_total:,.0f}"

    return {
        "days": series,
        "max_flow": max_flow,
        "has_flow": max_flow > 0,
        "channels": channels,
        "has_channels": solde_total > 0,
        "statuses": statuses,
        "status_total": status_total,
        "clients": clients,
        "window_days": days,
        "donut": donut,
        "donut_center": center,
        "donut_circ": circ,
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
