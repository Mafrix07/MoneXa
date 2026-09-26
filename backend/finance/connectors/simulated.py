"""Connecteurs SIMULÉS — données locales, pas d'API T-Money / Moov / banque."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from .base import FinancialConnector, NormalizedTransaction


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class _SimulatedWalletConnector(FinancialConnector):
    kind = "WALLET"
    is_simulated = True
    channel = "TMONEY"
    seed_rows: list[dict] = []

    def fetch_accounts(self) -> list[dict]:
        return [{"channel": self.channel, "simulated": True, "label": self.kind}]

    def fetch_transactions(self, cursor: Optional[str] = None) -> tuple[list[Any], Optional[str]]:
        # Snapshot simulé : on renvoie le jeu local. L'idempotence est sur provider_ref.
        rows = list(self.seed_rows)
        next_cursor = rows[-1]["external_id"] if rows else cursor
        return rows, next_cursor

    def normalize(self, transaction: Any) -> NormalizedTransaction:
        if isinstance(transaction, NormalizedTransaction):
            return transaction
        return NormalizedTransaction(
            source=self.channel,
            external_id=str(transaction["external_id"]),
            direction=str(transaction.get("direction", "IN")),
            amount=Decimal(str(transaction["amount"])),
            currency=str(transaction.get("currency", "XOF")),
            counterparty=str(transaction.get("counterparty", "")),
            reference=str(transaction.get("reference") or transaction["external_id"]),
            occurred_at=_parse_dt(str(transaction["occurred_at"])),
            status=str(transaction.get("status", "COMPLETED")),
            phone=str(transaction.get("phone", "")),
            raw_payload={"simulated": True, "raw": transaction},
        )


class TMoneyConnector(_SimulatedWalletConnector):
    kind = "TMONEY"
    channel = "TMONEY"
    seed_rows = [
        {
            "external_id": "TMXSEED001",
            "amount": "25000",
            "counterparty": "Kossi Mensah",
            "reference": "TMXSEED001",
            "occurred_at": "2026-09-24T10:00:00+00:00",
            "phone": "+228 90 11 22 33",
        },
    ]


class MoovConnector(_SimulatedWalletConnector):
    kind = "MOOV"
    channel = "MOOV"
    seed_rows = [
        {
            "external_id": "MV849321",
            "amount": "50000",
            "counterparty": "ABC Services",
            "reference": "MV849321",
            "occurred_at": "2026-09-25T09:15:00+00:00",
            "phone": "+228 92 00 11 22",
        },
    ]


# Flooz et Moov Money sont la même entité (Moov Africa)
FloozConnector = MoovConnector


class BankConnector(_SimulatedWalletConnector):
    kind = "BANQUE"
    channel = "BANQUE"
    seed_rows: list[dict] = []


class CashConnector(_SimulatedWalletConnector):
    kind = "ESPECES"
    channel = "ESPECES"
    seed_rows: list[dict] = []
