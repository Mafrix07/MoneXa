"""Excel/CSV export — pure stdlib to keep the dependency footprint small."""
from __future__ import annotations

import csv
import io
from typing import Iterable

from finance.models import Payment


PAYMENT_FIELDS = (
    "provider_ref", "amount", "channel", "payer_name", "payer_phone",
    "paid_at", "status", "match_method", "ai_confidence", "anomaly_score",
)


def export_payments_csv(queryset: Iterable[Payment]) -> bytes:
    """Export payments as CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(PAYMENT_FIELDS)
    for p in queryset:
        writer.writerow([
            p.provider_ref, p.amount, p.channel,
            p.payer_name or "", p.payer_phone or "",
            p.paid_at.isoformat() if p.paid_at else "",
            p.status, p.match_method,
            p.ai_confidence, p.anomaly_score,
        ])
    return buf.getvalue().encode("utf-8")


def export_excel(queryset: Iterable[Payment]) -> bytes:
    """Excel export via openpyxl if available, else CSV."""
    try:
        from openpyxl import Workbook
    except ImportError:
        return export_payments_csv(queryset)

    wb = Workbook()
    ws = wb.active
    ws.title = "Paiements"
    ws.append(list(PAYMENT_FIELDS))
    for p in queryset:
        ws.append([
            p.provider_ref, float(p.amount), p.channel,
            p.payer_name or "", p.payer_phone or "",
            p.paid_at.replace(tzinfo=None) if p.paid_at else None,
            p.status, p.match_method,
            float(p.ai_confidence or 0), float(p.anomaly_score or 0),
        ])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


__all__ = ["export_excel", "export_payments_csv"]
