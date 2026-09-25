"""Import CSV/Excel → NormalizedTransaction. Pas d'API bancaire."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from .base import FinancialConnector, NormalizedTransaction


class CSVConnector(FinancialConnector):
    kind = "CSV"
    is_simulated = True

    def __init__(self, content: bytes | str = b"", channel: str = "BANQUE"):
        if isinstance(content, bytes):
            self.text = content.decode("utf-8-sig", errors="replace")
        else:
            self.text = content
        self.channel = channel

    def fetch_transactions(self, cursor: Optional[str] = None) -> tuple[list[Any], Optional[str]]:
        reader = csv.DictReader(io.StringIO(self.text), delimiter=";")
        if reader.fieldnames is None:
            reader = csv.DictReader(io.StringIO(self.text), delimiter=",")
        rows = [dict(r) for r in reader]
        return rows, cursor

    def normalize(self, transaction: Any) -> NormalizedTransaction:
        if isinstance(transaction, NormalizedTransaction):
            return transaction
        row = {str(k).strip().lower(): (v or "").strip() for k, v in transaction.items()}
        ref = row.get("reference") or row.get("external_id") or row.get("provider_ref") or ""
        if not ref:
            raise ValueError("CSV: colonne reference / external_id obligatoire.")
        amount_raw = row.get("amount") or row.get("montant") or "0"
        amount_raw = amount_raw.replace(" ", "").replace(",", ".")
        try:
            amount = Decimal(amount_raw)
        except InvalidOperation as exc:
            raise ValueError(f"CSV: montant invalide ({amount_raw})") from exc
        occurred = row.get("occurred_at") or row.get("date") or row.get("paid_at")
        if occurred:
            dt = datetime.fromisoformat(occurred.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        source = (row.get("source") or row.get("channel") or self.channel).upper()
        if source in ("T-MONEY", "T MONEY"):
            source = "TMONEY"
        return NormalizedTransaction(
            source=source,
            external_id=row.get("external_id") or ref,
            direction=(row.get("direction") or "IN").upper(),
            amount=amount,
            currency=row.get("currency") or "XOF",
            counterparty=row.get("counterparty") or row.get("payer_name") or "",
            reference=ref,
            occurred_at=dt,
            status=row.get("status") or "COMPLETED",
            phone=row.get("phone") or "",
            raw_payload={"csv": transaction},
        )
