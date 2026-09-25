"""Fixtures SMS / ticket Mobile Money — 6 exemples de démo (données fictives)."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from finance.services.ai_pipeline import extract_payment_from_text

SMS_TMONEY_SMALL = """T-Money: Vous avez recu 3500 FCFA de AWA EXEMPLE (000 11 00 00 01). Ref TX2049183 le 24/09/2026 a 09h12. Solde: 18200 F. Merci"""

SMS_TMONEY_MEDIUM = """TOGOCEL T-MONEY Paiement recu 45 000FCFA de KOSSI FICTIF 0002200002 ID:TX77120459 le 25/09/2026 14:38 Nouveau solde 312500 FCFA. Ne communiquez jamais votre code"""

SMS_MOOV_MEDIUM = """Moov Money: Credit de 85000 F CFA recu de DEMO PAYEUR (000-33-00-00-03). Trans TXM88200144 Date 25/09/26 11h05. Frais 0. Info 111"""

SMS_MOOV_LARGE = """MOOV MONEY ALERTE: vous avez recu 750000FCFA de CLIENT TESTEUR 0004400004. Ref TX900145778 25-09-2026 16:21. Canal Moov Money. Conservez ce SMS"""

SMS_DEGRADED = """t money  vs  avez  recu   125 000fcfa  de  MENSAH  DEMO   0005500005   ref:  tx  44120987   le  23 09 2026  08 h 47   solde maj   merci tmoney"""

TICKET_PAPIER = """
            MOOV MONEY
         TICKET DE PAIEMENT
--------------------------------
Agence / Agent : DEMO KIOSK 12
Date : 22/09/2026    Heure : 17:03
--------------------------------
Type        : ENCAISSEMENT
Montant     : 210 000 FCFA
Payeur      : ADJOVI FICTIVE
Tel payeur  : 000 66 00 00 06
Ref txn     : TX61208801
Canal       : Moov Money
--------------------------------
Agent : 000-AGENT-DEMO
   Conservez ce ticket
"""

CASES = [
    (
        "tmoney_petit",
        SMS_TMONEY_SMALL,
        Decimal("3500"),
        "TX2049183",
        "TMONEY",
        "AWA EXEMPLE",
        datetime(2026, 9, 24, 9, 12, tzinfo=timezone.utc),
    ),
    (
        "tmoney_moyen",
        SMS_TMONEY_MEDIUM,
        Decimal("45000"),
        "TX77120459",
        "TMONEY",
        "KOSSI FICTIF",
        datetime(2026, 9, 25, 14, 38, tzinfo=timezone.utc),
    ),
    (
        "moov_moyen",
        SMS_MOOV_MEDIUM,
        Decimal("85000"),
        "TXM88200144",
        "MOOV",
        "DEMO PAYEUR",
        datetime(2026, 9, 25, 11, 5, tzinfo=timezone.utc),
    ),
    (
        "moov_gros",
        SMS_MOOV_LARGE,
        Decimal("750000"),
        "TX900145778",
        "MOOV",
        "CLIENT TESTEUR",
        datetime(2026, 9, 25, 16, 21, tzinfo=timezone.utc),
    ),
    (
        "sms_degrade",
        SMS_DEGRADED,
        Decimal("125000"),
        "TX44120987",
        "TMONEY",
        "MENSAH DEMO",
        datetime(2026, 9, 23, 8, 47, tzinfo=timezone.utc),
    ),
    (
        "ticket_papier",
        TICKET_PAPIER,
        Decimal("210000"),
        "TX61208801",
        "MOOV",
        "ADJOVI FICTIVE",
        datetime(2026, 9, 22, 17, 3, tzinfo=timezone.utc),
    ),
]


@pytest.mark.parametrize(
    "label,raw,montant,reference,canal,emetteur,paid_at",
    CASES,
    ids=[c[0] for c in CASES],
)
def test_six_mobile_money_fixtures(label, raw, montant, reference, canal, emetteur, paid_at):
    result = extract_payment_from_text(raw)
    assert result["montant"] == montant, label
    assert result["reference"] == reference, label
    assert result["operator"] == canal, label
    assert emetteur in (result["emetteur"] or "").upper(), label
    assert result["date_paiement"] == paid_at, label
    assert result["raw_text"].startswith("[SMS]")
