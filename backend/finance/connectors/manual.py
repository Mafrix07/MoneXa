"""Saisie manuelle → NormalizedTransaction."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from .base import FinancialConnector, NormalizedTransaction


class ManualConnector(FinancialConnector):
    kind = "MANUAL"
    is_simulated = True

    def fetch_transactions(self, cursor: Optional[str] = None) -> tuple[list[Any], Optional[str]]:
        return [], cursor

    def normalize(self, transaction: Any) -> NormalizedTransaction:
        if isinstance(transaction, NormalizedTransaction):
            return transaction
        paid_at = transaction.get("paid_at") or datetime.now(timezone.utc)
        if isinstance(paid_at, str):
            paid_at = datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
        return NormalizedTransaction(
            source=str(transaction.get("channel") or transaction.get("source") or "ESPECES"),
            external_id=str(transaction["provider_ref"]),
            direction="IN",
            amount=Decimal(str(transaction["amount"])),
            currency="XOF",
            counterparty=str(transaction.get("payer_name") or ""),
            reference=str(transaction["provider_ref"]),
            occurred_at=paid_at,
            phone=str(transaction.get("payer_phone") or ""),
            raw_payload={"manual": True},
        )
