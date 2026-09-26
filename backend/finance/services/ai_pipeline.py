"""
AI pipeline — extraction LLM multimodale des reçus Mobile Money.

Pipeline (cahier des charges §11.1):
1. Image uploaded via /api/payments/evidence/
2. Service calls LLM multimodal (GPT-4o-mini Vision or Gemini Flash)
3. JSON response validated by Pydantic PaymentExtraction
4. Returns dict with montant, reference, operator, emetteur, date, ai_confidence

Sans clé API : le collage SMS est parsé réellement (regex).
Les images exigent OPENAI_API_KEY ou GEMINI_API_KEY.
MONEXA_AI_FALLBACK_MOCK=1 est réservé à pytest.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finance.services.llm import chat_json, llm_configured, mock_fallback_enabled
from finance.services.sms_parser import parse_sms_text


VISION_SYSTEM = (
    "Tu es un assistant d'extraction de données de reçus mobile money ouest-africains "
    "(T-Money, Moov Money). "
    "N'invente jamais. Si une information n'est pas visible, retourne null pour ce champ. "
    "Réponds uniquement en JSON avec les clés: montant, reference, operator, "
    "type_operation, emetteur, telephone_emetteur, date_paiement."
)

VISION_USER = """Analyse cette image de SMS ou reçu Mobile Money.

Schéma JSON:
{
  "montant": number (FCFA, > 0) | null,
  "reference": string (référence opérateur) | null,
  "operator": "TMONEY" | "MOOV" | null,
  "type_operation": "PAIEMENT",
  "emetteur": string (nom du payeur) | null,
  "telephone_emetteur": string | null,
  "date_paiement": ISO-8601 | null
}

Few-shots de formats:
- T-Money: "Vous avez recu 50 000 FCFA de KOSSI MENSAH. Ref: TMX8847291023"
- Moov Money: "Moov Money: credit 25000F de AFI ADJOVI ID MV19283746" ou "Flooz paiement 10000 FCFA recu. Ref FL5544332211"

N'invente aucune référence ni aucun montant."""

TEXT_SYSTEM = (
    "Tu extraits des champs d'un SMS Mobile Money togolais. "
    "N'invente jamais. JSON uniquement, mêmes clés que pour une image."
)


class PaymentExtraction(BaseModel):
    """Strict schema for AI-extracted payment data. Any malformed field → reject."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    montant: Decimal = Field(..., gt=0, description="Montant en FCFA, strictement positif")
    reference: str = Field(..., min_length=3, max_length=50,
                            description="Référence opérateur (provider_ref)")
    operator: str = Field(..., description="TMONEY | MOOV")
    type_operation: str = Field(default="PAIEMENT", description="Type d'opération")
    emetteur: str = Field(..., min_length=2, max_length=200, description="Nom du payeur")
    telephone_emetteur: Optional[str] = Field(default=None, max_length=20)
    date_paiement: datetime = Field(..., description="Date de la transaction")

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        v_up = v.upper().strip()
        mapping = {
            "T-MONEY": "TMONEY", "TMONEY": "TMONEY", "T MONEY": "TMONEY",
            "MOOV": "MOOV", "MOOV MONEY": "MOOV", "MOOV-MONEY": "MOOV",
            "FLOOZ": "MOOV",
        }
        if v_up not in mapping:
            raise ValueError(f"Opérateur inconnu: {v}. Attendu: TMONEY, MOOV.")
        return mapping[v_up]

    @field_validator("date_paiement")
    @classmethod
    def validate_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > datetime.now(timezone.utc) + timedelta(days=1):
            raise ValueError("Date de paiement dans le futur.")
        if v.year < 2020:
            raise ValueError("Date de paiement trop ancienne.")
        return v


def _to_result(extraction: PaymentExtraction, *, ai_confidence: float, raw_text: str) -> dict:
    return {
        "montant": extraction.montant,
        "reference": extraction.reference,
        "operator": extraction.operator,
        "emetteur": extraction.emetteur,
        "telephone_emetteur": extraction.telephone_emetteur,
        "date_paiement": extraction.date_paiement,
        "ai_confidence": ai_confidence,
        "raw_text": raw_text,
        "extraction": extraction,
    }


def _merge_partial(base: dict, extra: dict) -> dict:
    merged = dict(base)
    for key, value in extra.items():
        if merged.get(key) in (None, "") and value not in (None, ""):
            merged[key] = value
    return merged


def _extraction_from_partial(partial: dict) -> PaymentExtraction:
    data = dict(partial)
    if data.get("monexa_ref") and not data.get("operator"):
        data["operator"] = "TMONEY"
    if data.get("monexa_ref") and not data.get("reference"):
        data["reference"] = data["monexa_ref"]
    if not data.get("emetteur"):
        data["emetteur"] = "Payeur inconnu"
    if not data.get("date_paiement"):
        data["date_paiement"] = datetime.now(timezone.utc)
    if not data.get("type_operation"):
        data["type_operation"] = "PAIEMENT"
    if not data.get("montant") or not data.get("reference") or not data.get("operator"):
        missing = [k for k in ("montant", "reference", "operator") if not data.get(k)]
        raise ValueError(
            "Extraction incomplète (champs manquants: "
            + ", ".join(missing)
            + "). Saisissez le SMS complet ou photographiez un reçu lisible."
        )
    data.pop("monexa_ref", None)
    return PaymentExtraction.model_validate(data)


def _llm_extract(*, user: str, image_bytes: Optional[bytes] = None) -> dict:
    payload = chat_json(
        system=VISION_SYSTEM if image_bytes else TEXT_SYSTEM,
        user=user,
        image_bytes=image_bytes,
        timeout=20,
    )
    # Normalise nulls
    cleaned = {k: (None if v in ("", "null", "None") else v) for k, v in payload.items()}
    if "montant" in cleaned and cleaned["montant"] is not None:
        cleaned["montant"] = Decimal(str(cleaned["montant"]).replace(" ", "").replace(",", "."))
    return cleaned


def _deterministic_mock(image_bytes: bytes) -> PaymentExtraction:
    """Réservé à pytest (MONEXA_AI_FALLBACK_MOCK=1)."""
    digest = hashlib.sha256(image_bytes).hexdigest()
    seed = int(digest[:8], 16)
    amount = (seed % 980_000) + 5_000
    operators = ["TMONEY", "MOOV"]
    operator = operators[int(digest[8:10], 16) % len(operators)]
    prefix_map = {"TMONEY": "TMX", "MOOV": "MV"}
    names = [
        "Kossi Mensah", "Afi Adjovi", "Koffi Agbessi", "Mensah Kossi",
        "Adzo Komla", "Komi Agbélo", "Awa Tchalla", "Yaovi Dotse",
    ]
    payer = names[int(digest[20:22], 16) % len(names)]
    days_ago = int(digest[42:44], 16) % 30
    paid_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return PaymentExtraction(
        montant=Decimal(amount),
        reference=f"{prefix_map[operator]}{digest[10:20].upper()}",
        operator=operator,
        type_operation="PAIEMENT",
        emetteur=payer,
        telephone_emetteur="+228 90 12 34 56",
        date_paiement=paid_at,
    )


def extract_payment_from_image(image_bytes: bytes, filename: str = "") -> dict:
    if not image_bytes:
        raise ValueError("Image vide.")

    if llm_configured():
        try:
            partial = _llm_extract(user=VISION_USER, image_bytes=image_bytes)
        except Exception as exc:
            raise ValueError(
                f"Échec de l'extraction Vision: {exc}. "
                "Vérifiez la clé API ou collez le texte du SMS (fallback)."
            ) from exc
        extraction = _extraction_from_partial(partial)
        raw = (
            f"[LLM VISION] {extraction.emetteur} {extraction.montant} FCFA "
            f"{extraction.operator} réf {extraction.reference} fichier={filename}"
        )
        return _to_result(extraction, ai_confidence=0.92, raw_text=raw)

    if mock_fallback_enabled():
        extraction = _deterministic_mock(image_bytes)
        raw = (
            f"[TEST MOCK] Paiement reçu de {extraction.emetteur}, "
            f"montant {extraction.montant} FCFA via {extraction.operator}. "
            f"Réf: {extraction.reference}."
        )
        return _to_result(extraction, ai_confidence=0.85, raw_text=raw)

    raise ValueError(
        "Extraction d'image impossible sans LLM. "
        "Ajoutez OPENAI_API_KEY ou GEMINI_API_KEY dans backend/.env, "
        "ou utilisez POST /api/payments/manual-text/ avec le SMS."
    )


def extract_payment_from_text(text: str) -> dict:
    text = (text or "").strip()
    if len(text) < 8:
        raise ValueError("Texte SMS trop court.")

    parsed = parse_sms_text(text)
    if llm_configured() and (
        not parsed.get("montant") or not parsed.get("reference") or not parsed.get("operator")
    ):
        try:
            llm_part = _llm_extract(user=f"SMS:\n{text}\n\n{VISION_USER}")
            parsed = _merge_partial(parsed, llm_part)
        except Exception:
            pass

    extraction = _extraction_from_partial(parsed)
    return _to_result(
        extraction,
        ai_confidence=0.88 if parsed.get("montant") and parsed.get("reference") else 0.7,
        raw_text=f"[SMS] {text}",
    )


__all__ = [
    "PaymentExtraction",
    "extract_payment_from_image",
    "extract_payment_from_text",
]
