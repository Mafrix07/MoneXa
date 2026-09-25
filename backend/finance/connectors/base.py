"""Abstraction FinancialConnector + schéma interne normalisé."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable, Optional


@dataclass
class NormalizedTransaction:
    """Format interne commun — le reste de MoneXa ne voit que ceci."""

    source: str
    external_id: str
    direction: str  # IN | OUT
    amount: Decimal
    currency: str
    counterparty: str
    reference: str
    occurred_at: datetime
    status: str = "COMPLETED"
    phone: str = ""
    raw_payload: dict = field(default_factory=dict)

    def to_ledger_fields(self) -> dict:
        return {
            "provider_ref": self.reference or self.external_id,
            "amount": self.amount,
            "channel": self.source,
            "payer_name": self.counterparty,
            "payer_phone": self.phone,
            "paid_at": self.occurred_at,
            "raw_text": str(self.raw_payload.get("raw_text") or self.raw_payload),
        }


class FinancialConnector(ABC):
    """
    Contrat d'un connecteur.

    authenticate / fetch_* : no-op ou simulation selon l'implémentation.
    normalize : obligatoire — produit un NormalizedTransaction.
    """

    kind: str = "UNKNOWN"
    is_simulated: bool = True

    def authenticate(self) -> bool:
        return True

    def fetch_accounts(self) -> list[dict]:
        return []

    def fetch_transactions(self, cursor: Optional[str] = None) -> tuple[list[Any], Optional[str]]:
        return [], cursor

    @abstractmethod
    def normalize(self, transaction: Any) -> NormalizedTransaction:
        raise NotImplementedError

    def health_check(self) -> dict:
        return {
            "kind": self.kind,
            "ok": True,
            "simulated": self.is_simulated,
            "detail": (
                "Connecteur simulé — aucune API opérateur n'est appelée."
                if self.is_simulated
                else "Connecteur opérationnel."
            ),
        }

    def iter_normalized(self, cursor: Optional[str] = None) -> Iterable[NormalizedTransaction]:
        rows, _ = self.fetch_transactions(cursor=cursor)
        for row in rows:
            yield self.normalize(row)
