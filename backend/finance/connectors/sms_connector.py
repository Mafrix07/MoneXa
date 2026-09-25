"""SMS brut → NormalizedTransaction via le parseur existant."""
from __future__ import annotations

from typing import Any, Optional

from finance.services.ai_pipeline import extract_payment_from_text

from .base import FinancialConnector, NormalizedTransaction


class SMSConnector(FinancialConnector):
    kind = "SMS"
    is_simulated = True

    def __init__(self, text: str = ""):
        self.text = text

    def fetch_transactions(self, cursor: Optional[str] = None) -> tuple[list[Any], Optional[str]]:
        if not self.text.strip():
            return [], cursor
        return [self.text], cursor

    def normalize(self, transaction: Any) -> NormalizedTransaction:
        if isinstance(transaction, NormalizedTransaction):
            return transaction
        extracted = extract_payment_from_text(str(transaction))
        return NormalizedTransaction(
            source=extracted["operator"],
            external_id=extracted["reference"],
            direction="IN",
            amount=extracted["montant"],
            currency="XOF",
            counterparty=extracted["emetteur"],
            reference=extracted["reference"],
            occurred_at=extracted["date_paiement"],
            phone=extracted.get("telephone_emetteur") or "",
            raw_payload={"raw_text": extracted.get("raw_text", str(transaction))},
        )
