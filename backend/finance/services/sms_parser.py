"""
Parseur déterministe des SMS Mobile Money (T-Money, Moov Money).

Utilisé comme extraction réelle hors LLM (collage SMS / OCR ticket).
Ne fabrique jamais de référence ni de montant manquants.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional


_AMOUNT = re.compile(
    r"(?:montant|recu|reçu|credit|crédité|debit|débit)?"
    r"[^\d]{0,32}(\d{1,3}(?:[\s.\u00a0]\d{3})+|\d+)(?:[.,](\d{1,2}))?"
    r"\s*(?:FCFA|F\s*CFA|XOF|F CFA)",
    re.IGNORECASE,
)
_AMOUNT_ALT = re.compile(
    r"(\d{1,3}(?:[\s.\u00a0]\d{3})+|\d{3,})(?:[.,](\d{1,2}))?\s*(?:FCFA|F\s*CFA|XOF)",
    re.IGNORECASE,
)
_REF_LABELED = re.compile(
    r"(?:ref(?:[eé]rence)?|txn|trans(?:action)?|id)\s*[:#.\-]*\s*"
    r"((?:TX|TMX|TM|MV|MOOV|FL|FLZ|TXN|TXM)[\s\-]*[A-Z0-9]{4,})",
    re.IGNORECASE,
)
_REF_BARE = re.compile(
    r"\b((?:TMX|TXM|TXN|TX|MV|MOOV|FLZ|FL)[\s\-]*[A-Z0-9]{5,})\b",
    re.IGNORECASE,
)
_DATE_SEP = re.compile(
    r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})"
    r"(?:[ Tàa]*(\d{1,2})\s*[:hH]\s*(\d{2}))?",
    re.IGNORECASE,
)
_DATE_SPACED = re.compile(
    r"(?:le|date)?\s*(\d{1,2})\s+(\d{1,2})\s+(\d{4})"
    r"(?:[ Tàa]*(\d{1,2})\s*[:hH]\s*(\d{2}))?",
    re.IGNORECASE,
)
_TIME_ONLY = re.compile(
    r"(?:heure|h(?:eure)?)\s*[:\-]?\s*(\d{1,2})\s*[:hH]\s*(\d{2})",
    re.IGNORECASE,
)
_PHONE = re.compile(
    r"(?:\+?228[\s.\-]*)?(?:0)?([79]\d(?:[\s.\-]?\d{2}){3})",
)


def _normalize_ref(raw: str) -> str:
    return re.sub(r"[\s\-]+", "", raw).upper()


def _parse_amount(text: str) -> Optional[Decimal]:
    match = _AMOUNT.search(text) or _AMOUNT_ALT.search(text)
    if not match:
        return None
    whole = re.sub(r"[\s.\u00a0]", "", match.group(1))
    frac = match.group(2) or "00"
    try:
        value = Decimal(f"{whole}.{frac}")
    except InvalidOperation:
        return None
    return value if value > 0 else None


def detect_operator(text: str) -> Optional[str]:
    compact = re.sub(r"\s+", " ", text.upper())
    if any(tok in compact for tok in ("T-MONEY", "TMONEY", "T MONEY", "TMX", "TOGOCEL")):
        return "TMONEY"
    if "MOOV" in compact or "FLOOZ" in compact or re.search(r"\b(?:MV|FL)[A-Z0-9]{5,}", compact):
        return "MOOV"
    return None


def _datetime_from_groups(match: re.Match, text: str) -> Optional[datetime]:
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if year < 100:
        year += 2000
    if not (1 <= month <= 12 and 1 <= day <= 31 and year >= 2020):
        return None
    hour, minute = match.group(4), match.group(5)
    if hour is None:
        time_m = _TIME_ONLY.search(text)
        if time_m:
            hour, minute = time_m.group(1), time_m.group(2)
    hh = int(hour) if hour is not None else 12
    mm = int(minute) if minute is not None else 0
    try:
        return datetime(year, month, day, hh, mm, tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_date(text: str) -> Optional[datetime]:
    for pattern in (_DATE_SEP, _DATE_SPACED):
        for match in pattern.finditer(text):
            parsed = _datetime_from_groups(match, text)
            if parsed:
                return parsed
    return None


def _parse_payer(text: str) -> Optional[str]:
    patterns = [
        r"(?:payeur|emetteur|émetteur|expediteur|expéditeur)\s*[:\-]?\s*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ '\-]{1,60})",
        r"(?:recu|reçu)\s+de\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ '\-]{1,60})",
        r"\bde\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿ '\-]{1,60})",
        r"(?:client)\s*[:\-]?\s*([A-ZÀ-Ÿ][A-Za-zÀ-ÿ '\-]{1,60})",
    ]
    for pat in patterns:
        found = re.search(pat, text, re.IGNORECASE)
        if not found:
            continue
        name = re.split(
            r"[\(\n]|tel|tél|ref|id:|\bid\b|000",
            found.group(1),
            maxsplit=1,
            flags=re.I,
        )[0].strip(" .:-")
        name = re.sub(r"\s+", " ", name)
        if len(name) >= 2 and not re.fullmatch(r"\d+", name):
            return name.upper()
    return None


def parse_sms_text(text: str) -> dict:
    """Champs absents = None. MXA extraite telle quelle, jamais inventée."""
    from finance.services.matcher import extract_mxa_ref

    text = (text or "").strip()
    ref_m = _REF_LABELED.search(text) or _REF_BARE.search(text)
    reference = _normalize_ref(ref_m.group(1)) if ref_m else None
    monexa_ref = extract_mxa_ref(text)
    operator = detect_operator(text)
    emetteur = _parse_payer(text)
    if monexa_ref and not operator:
        operator = "TMONEY"
    if monexa_ref and not emetteur:
        emetteur = "Payeur inconnu"
    if monexa_ref and not reference:
        reference = monexa_ref
    return {
        "montant": _parse_amount(text),
        "reference": reference,
        "monexa_ref": monexa_ref,
        "operator": operator,
        "emetteur": emetteur,
        "telephone_emetteur": None,
        "date_paiement": _parse_date(text),
    }
