"""
Tests de la détection d'anomalies — règles déterministes.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone as dj_timezone

from accounts.models import User, Role
from finance.models import (
    Invoice, Payment, Channel, InvoiceStatus, PaymentStatus, MatchMethod,
)
from finance.services.anomalies import detect_anomalies


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="anom@test.tg", password="X", role=Role.CAISSIER,
    )


@pytest.fixture
def invoice(user):
    return Invoice.objects.create(
        reference=Invoice.generate_reference(),
        client_name="Client Test",
        client_phone="+228 90 12 34 56",
        amount=Decimal("100000"),
        issue_date=dj_timezone.now().date() - timedelta(days=5),
        due_date=dj_timezone.now().date() + timedelta(days=10),
        status=InvoiceStatus.EN_ATTENTE,
        created_by=user,
    )


@pytest.mark.django_db
def test_ecart_montant_rule(user, invoice):
    """Règle écart montant : paiement != montant facture."""
    payment = Payment.objects.create(
        provider_ref="TMX_ECART_REF",
        amount=Decimal("95000"),  # different from invoice 100000
        channel=Channel.TMONEY,
        payer_name="Client Test",
        paid_at=dj_timezone.now(),
        invoice=invoice,
        status=PaymentStatus.RECONCILIE,
        match_method=MatchMethod.MANUEL,
        created_by=user,
    )
    anomalies = detect_anomalies(payment)
    types = [a["type"] for a in anomalies]
    assert any("Écart" in t for t in types)


@pytest.mark.django_db
def test_sans_facture_rule(user):
    """Règle paiement sans facture : payment sans invoice."""
    payment = Payment.objects.create(
        provider_ref="TMX_NO_FACT",
        amount=Decimal("50000"),
        channel=Channel.TMONEY,
        payer_name="Random Person",
        paid_at=dj_timezone.now(),
        status=PaymentStatus.NON_RATTACHE,
        match_method=MatchMethod.MANUEL,
        created_by=user,
    )
    anomalies = detect_anomalies(payment)
    types = [a["type"] for a in anomalies]
    assert any("sans facture" in t.lower() for t in types)


@pytest.mark.django_db
def test_hors_fenetre_rule(user, invoice):
    """Règle hors fenêtre : paiement avant la facture."""
    payment = Payment.objects.create(
        provider_ref="TMX_HORS_FEN",
        amount=Decimal("100000"),
        channel=Channel.TMONEY,
        payer_name="Client Test",
        paid_at=dj_timezone.now() - timedelta(days=10),  # avant issue_date
        invoice=invoice,
        status=PaymentStatus.RECONCILIE,
        match_method=MatchMethod.MANUEL,
        created_by=user,
    )
    anomalies = detect_anomalies(payment)
    types = [a["type"] for a in anomalies]
    assert any("fenêtre" in t.lower() for t in types)


@pytest.mark.django_db
def test_no_anomalies_on_clean_payment(user, invoice):
    """Un paiement propre ne déclenche aucune anomalie."""
    payment = Payment.objects.create(
        provider_ref="TMX_CLEAN_REF",
        amount=Decimal("100000"),  # matches invoice
        channel=Channel.TMONEY,
        payer_name="Client Test",
        paid_at=dj_timezone.now(),
        invoice=invoice,
        status=PaymentStatus.RECONCILIE,
        match_method=MatchMethod.AUTO_REF,
        created_by=user,
    )
    anomalies = detect_anomalies(payment)
    # The only "anomaly" should be a potential "Paiement nocturne" if hour >= 22 or < 6
    # Filter out informational ones
    serious = [a for a in anomalies if a["severity"] != "info"]
    assert len(serious) == 0


@pytest.mark.django_db
def test_nocturne_detection(user):
    """Un paiement à 03h du matin est détecté comme nocturne."""
    # Build a datetime explicitly at 3am
    morning = dj_timezone.now().replace(hour=3, minute=12, second=0, microsecond=0)
    payment = Payment.objects.create(
        provider_ref="TMX_NIGHT_REF",
        amount=Decimal("50000"),
        channel=Channel.TMONEY,
        payer_name="Late Payer",
        paid_at=morning,
        status=PaymentStatus.NON_RATTACHE,
        match_method=MatchMethod.MANUEL,
        created_by=user,
    )
    anomalies = detect_anomalies(payment)
    types = [a["type"] for a in anomalies]
    assert any("nocturne" in t.lower() for t in types)
