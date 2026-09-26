"""
Tests des KPIs du dashboard.
"""
import pytest
from decimal import Decimal
from datetime import timedelta, timezone
from django.utils import timezone as dj_timezone

from accounts.models import User, Role
from finance.models import Invoice, Payment, Channel, InvoiceStatus, PaymentStatus
from reporting.services import compute_kpis


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@test.tg", password="X", role=Role.CAISSIER,
    )


@pytest.mark.django_db
def test_kpis_returns_all_expected_keys(user):
    """compute_kpis retourne toutes les clés attendues (~15 KPIs)."""
    # Create some data
    Payment.objects.create(
        provider_ref="REF1",
        amount=Decimal("100000"),
        channel=Channel.TMONEY,
        payer_name="Test",
        paid_at=dj_timezone.now(),
        created_by=user,
    )

    kpis = compute_kpis()

    expected_keys = {
        "solde_total", "solde_par_canal",
        "encaisse_7j", "encaisse_30j", "decaisse_7j", "decaisse_30j",
        "flux_net_7j", "flux_net_30j",
        "factures_en_attente", "factures_en_retard",
        "paiements_a_valider", "nb_anomalies",
        "prevision_j7", "prevision_j30", "top_5_clients",
    }
    assert expected_keys.issubset(kpis.keys())


@pytest.mark.django_db
def test_solde_par_canal_aggregates_correctly(user):
    """Le solde par canal agrège correctement les paiements."""
    now = dj_timezone.now()
    Payment.objects.create(
        provider_ref="TMX1", amount=Decimal("100000"),
        channel=Channel.TMONEY, paid_at=now, created_by=user,
    )
    Payment.objects.create(
        provider_ref="TMX2", amount=Decimal("50000"),
        channel=Channel.TMONEY, paid_at=now, created_by=user,
    )
    Payment.objects.create(
        provider_ref="MV1", amount=Decimal("30000"),
        channel=Channel.MOOV, paid_at=now, created_by=user,
    )

    kpis = compute_kpis()
    assert kpis["solde_par_canal"]["TMONEY"] == 150_000.0
    assert kpis["solde_par_canal"]["MOOV"] == 30_000.0


@pytest.mark.django_db
def test_dashboard_charts_use_real_payment_amounts(user):
    now = dj_timezone.now()
    Payment.objects.create(
        provider_ref="CHART1",
        amount=Decimal("50000"),
        channel=Channel.TMONEY,
        payer_name="ABC SARL",
        paid_at=now,
        created_by=user,
        status=PaymentStatus.RECONCILIE,
    )
    kpis = compute_kpis()
    charts = kpis["charts"]
    today = charts["days"][-1]
    assert today["encaisse"] == 50000.0
    assert charts["has_flow"] is True
    assert charts["status_total"] == 1
    recon = next(s for s in charts["statuses"] if s["code"] == PaymentStatus.RECONCILIE)
    assert recon["count"] == 1
    assert charts["clients"][0]["name"] == "ABC SARL"
    assert charts["clients"][0]["total"] == 50000.0
    assert charts["period"][0]["value"] == 50000.0


@pytest.mark.django_db
def test_dashboard_endpoint_works(gerant_client):
    """L'endpoint /api/dashboard/summary/ répond correctement."""
    resp = gerant_client.get("/api/dashboard/summary/")
    assert resp.status_code == 200
    assert "solde_total" in resp.data
