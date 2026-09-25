"""Connecteurs simulés, normalisation, idempotence."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.utils import timezone as dj_timezone

from finance.connectors.csv_connector import CSVConnector
from finance.connectors.registry import get_connector
from finance.connectors.simulated import MoovConnector
from finance.models import Channel, Payment
from finance.services.ingest import ingest_normalized
from finance.services.sync import sync_source
from finance.services.demo_sources import ensure_default_sources
from finance.models import FinancialSource, SyncStatus


@pytest.mark.django_db
def test_moov_normalize_golden_row():
    c = MoovConnector()
    rows, _ = c.fetch_transactions()
    tx = c.normalize(rows[0])
    assert tx.source == "MOOV"
    assert tx.reference == "MV849321"
    assert tx.amount == Decimal("50000")
    assert tx.counterparty == "ABC Services"


@pytest.mark.django_db
def test_csv_normalize_and_invalid_amount():
    ok = "reference;amount;counterparty;occurred_at;source\nBK1;1000;Test;2026-09-25T10:00:00+00:00;BANQUE\n"
    tx = CSVConnector(ok).normalize(CSVConnector(ok).fetch_transactions()[0][0])
    assert tx.reference == "BK1"
    bad = "reference;amount\nBK2;abc\n"
    with pytest.raises(ValueError):
        CSVConnector(bad).normalize(CSVConnector(bad).fetch_transactions()[0][0])


@pytest.mark.django_db
def test_ingest_idempotent(caissier):
    c = MoovConnector()
    tx = c.normalize(c.fetch_transactions()[0][0])
    p1, created1 = ingest_normalized(tx, caissier)
    p2, created2 = ingest_normalized(tx, caissier)
    assert created1 is True
    assert created2 is False
    assert p1.id == p2.id
    assert Payment.objects.filter(provider_ref="MV849321").count() == 1


@pytest.mark.django_db
def test_sync_incremental_ignore(gerant):
    ensure_default_sources(gerant)
    src = FinancialSource.objects.get(connector_kind="MOOV")
    log1 = sync_source(src, gerant)
    assert log1.status == SyncStatus.SUCCESS
    assert log1.created_count >= 1
    log2 = sync_source(src, gerant)
    assert log2.created_count == 0
    assert log2.ignored_count >= 1


@pytest.mark.django_db
def test_health_declares_simulated():
    c = get_connector("TMONEY")
    h = c.health_check()
    assert h["simulated"] is True
    assert "API" in h["detail"] or "simul" in h["detail"].lower()
