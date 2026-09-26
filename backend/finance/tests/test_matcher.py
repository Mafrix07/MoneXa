"""
Tests de la cascade de matching — 4 niveaux.
"""
from datetime import timedelta, timezone
from decimal import Decimal

import pytest
from django.utils import timezone as dj_timezone

from accounts.models import User, Role
from finance.models import (
    Invoice, Payment, InvoiceStatus, PaymentStatus,
    MatchMethod, Channel,
)
from finance.services.matcher import match_payment, _similarity


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@test.tg", password="X", role=Role.CAISSIER,
    )


@pytest.fixture
def invoice(user):
    return Invoice.objects.create(
        reference=Invoice.generate_reference(),
        client_name="Kossi Mensah",
        client_phone="+228 90 12 34 56",
        amount=Decimal("100000"),
        issue_date=dj_timezone.now().date() - timedelta(days=2),
        due_date=dj_timezone.now().date() + timedelta(days=12),
        status=InvoiceStatus.EN_ATTENTE,
        created_by=user,
    )


@pytest.mark.django_db
def test_level_1_auto_ref(user, invoice):
    """Niveau 1: provider_ref contient FACT-* → A_VALIDER (pas d'auto sans MXA)."""
    payment = Payment.objects.create(
        provider_ref=f"TMX{invoice.reference}9999",
        amount=Decimal("100000"),
        channel=Channel.TMONEY,
        payer_name="Kossi Mensah",
        paid_at=dj_timezone.now(),
        created_by=user,
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert inv == invoice
    assert method == MatchMethod.AUTO_REF


@pytest.mark.django_db
def test_level_2_auto_montant(user, invoice):
    """Niveau 2: montant correspond, date dans la fenêtre 7 jours → A_VALIDER."""
    payment = Payment.objects.create(
        provider_ref="TMX_RANDOM_REF_2",
        amount=Decimal("100000"),  # matches invoice amount
        channel=Channel.TMONEY,
        payer_name="Different Name",
        paid_at=dj_timezone.now(),
        created_by=user,
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert inv == invoice
    assert method == MatchMethod.AUTO_MONTANT


@pytest.mark.django_db
def test_level_3_fuzzy_payer(user, invoice):
    """Niveau 3: similarité nom > 0.8 → A_VALIDER."""
    payment = Payment.objects.create(
        provider_ref="TMX_RANDOM_REF_3",
        amount=Decimal("50000"),  # different amount
        channel=Channel.TMONEY,
        payer_name="Kossi Mensah",  # exact match (similarity = 1.0)
        paid_at=dj_timezone.now(),
        created_by=user,
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.A_VALIDER
    assert inv == invoice
    assert method == MatchMethod.FUZZY


@pytest.mark.django_db
def test_level_4_non_rattache(user, invoice):
    """Niveau 4: aucune correspondance → NON_RATTACHE."""
    payment = Payment.objects.create(
        provider_ref="TMX_RANDOM_REF_4",
        amount=Decimal("75000"),
        channel=Channel.TMONEY,
        payer_name="Completely Different Person",
        payer_phone="+228 99 99 99 99",
        paid_at=dj_timezone.now(),
        created_by=user,
    )
    status, inv, method = match_payment(payment)
    assert status == PaymentStatus.NON_RATTACHE
    assert inv is None
    assert method == MatchMethod.MANUEL


def test_similarity_helper():
    """Le helper de similarité fonctionne correctement."""
    assert _similarity("Kossi Mensah", "Kossi Mensah") == 1.0
    assert _similarity("", "anything") == 0.0
    # Similarity for reversed strings is around 0.5 (SequenceMatcher)
    sim = _similarity("Kossi Mensah", "Mensah Kossi")
    assert 0.4 <= sim <= 1.0
    # Very different strings have low similarity
    assert _similarity("abc", "xyz") < 0.5
