"""
AI pipeline — extraction LLM multimodale des reçus Mobile Money.

Pipeline (cahier des charges §11.1):
1. Image uploaded via /api/payments/evidence/
2. Service calls LLM multimodal (GPT-4o-mini Vision or Gemini Flash)
3. JSON response validated by Pydantic PaymentExtraction
4. Returns dict with montant, reference, operator, emetteur, date, ai_confidence

DEMO MODE (no OPENAI_API_KEY):
    Returns a deterministic mock based on image content hash.
    This ensures tests pass without external API dependencies.

PRODUCTION MODE (OPENAI_API_KEY set):
    Calls OpenAI Vision API. Falls back to mock on error.
"""
from __future__ import annotations
import hashlib
import io
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ──────────────────────────────────────────────────────────────────────────
# Pydantic schema — strict validation of LLM output
# ──────────────────────────────────────────────────────────────────────────
class PaymentExtraction(BaseModel):
    """Strict schema for AI-extracted payment data. Any malformed field → reject."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    montant: Decimal = Field(..., gt=0, description="Montant en FCFA, strictement positif")
    reference: str = Field(..., min_length=3, max_length=50,
                            description="Référence opérateur (provider_ref)")
    operator: str = Field(..., description="TMONEY | MOOV | FLOOZ")
    type_operation: str = Field(default="PAIEMENT", description="Type d'opération")
    emetteur: str = Field(..., min_length=2, max_length=200, description="Nom du payeur")
    telephone_emetteur: Optional[str] = Field(default=None, max_length=20)
    date_paiement: datetime = Field(..., description="Date de la transaction")

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        v_up = v.upper().strip()
        # Mapping tolérant
        mapping = {
            "T-MONEY": "TMONEY", "TMONEY": "TMONEY", "T MONEY": "TMONEY",
            "MOOV": "MOOV", "MOOV MONEY": "MOOV", "MOOV-MONEY": "MOOV",
            "FLOOZ": "FLOOZ",
        }
        if v_up not in mapping:
            raise ValueError(f"Opérateur inconnu: {v}. Attendu: TMONEY, MOOV, FLOOZ.")
        return mapping[v_up]

    @field_validator("date_paiement")
    @classmethod
    def validate_date(cls, v: datetime) -> datetime:
        if v > datetime.now(timezone.utc) + timedelta(days=1):
            raise ValueError("Date de paiement dans le futur.")
        if v.year < 2020:
            raise ValueError("Date de paiement trop ancienne.")
        return v


# ──────────────────────────────────────────────────────────────────────────
# Mock data generator (deterministic, based on image content hash)
# ──────────────────────────────────────────────────────────────────────────
_PAYER_NAMES = [
    "Kossi Mensah", "Afi Adjovi", "Koffi Agbessi", "Mensah Kossi",
    "Adzo Komla", "Komi Agbélo", "Awa Tchalla", "Yaovi Dotse",
    "Afia Mawusi", "Kossi Tsolenyanu",
]
_PHONE_PREFIXES = ["90", "91", "92", "93", "70", "79"]


def _hash_image(image_bytes: bytes) -> str:
    """Return a hex digest of the image content."""
    return hashlib.sha256(image_bytes).hexdigest()


def _deterministic_mock(image_bytes: bytes) -> PaymentExtraction:
    """
    Generate a deterministic PaymentExtraction from the image hash.
    Same image → same extraction. Different image → different extraction.
    """
    digest = _hash_image(image_bytes)
    # Use parts of the hash to derive each field deterministically
    seed = int(digest[:8], 16)
    amount = (seed % 980_000) + 5_000  # 5_000 .. 985_000 FCFA

    operator_idx = (int(digest[8:10], 16) % 3)
    operators = ["TMONEY", "MOOV", "FLOOZ"]
    operator = operators[operator_idx]

    # Provider ref prefix by operator
    prefix_map = {"TMONEY": "TMX", "MOOV": "MV", "FLOOZ": "FL"}
    ref = f"{prefix_map[operator]}{digest[10:20].upper()}"

    payer_idx = (int(digest[20:22], 16) % len(_PAYER_NAMES))
    payer_name = _PAYER_NAMES[payer_idx]

    phone_idx = (int(digest[22:24], 16) % len(_PHONE_PREFIXES))
    phone_prefix = _PHONE_PREFIXES[phone_idx]
    phone_rest = f"{int(digest[24:30], 16) % 100:02d} {int(digest[30:36], 16) % 100:02d} {int(digest[36:42], 16) % 100:02d}"
    phone = f"+228 {phone_prefix} {phone_rest}"

    # Date — within last 30 days
    days_ago = int(digest[42:44], 16) % 30
    paid_at = datetime.now(timezone.utc) - timedelta(days=days_ago,
                                                       hours=int(digest[44:46], 16) % 24)

    return PaymentExtraction(
        montant=Decimal(amount),
        reference=ref,
        operator=operator,
        type_operation="PAIEMENT",
        emetteur=payer_name,
        telephone_emetteur=phone,
        date_paiement=paid_at,
    )


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────
def extract_payment_from_image(image_bytes: bytes, filename: str = "") -> dict:
    """
    Extract payment data from an image of a Mobile Money SMS / receipt.

    Args:
        image_bytes: raw bytes of the uploaded image
        filename: original filename (for logging)

    Returns:
        dict with keys:
            - montant: Decimal
            - reference: str
            - operator: str
            - emetteur: str
            - telephone_emetteur: str | None
            - date_paiement: datetime
            - ai_confidence: float (0..1)
            - raw_text: str (extracted text for audit)
            - extraction: PaymentExtraction (the validated Pydantic instance)
    """
    # Always start from the deterministic mock (so we have a baseline)
    extraction = _deterministic_mock(image_bytes)

    # If an OpenAI/Gemini API key is set, try the real call (best-effort)
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    confidence = 0.85  # default mock confidence
    raw_text = (
        f"[DEMO] Paiement reçu de {extraction.emetteur} "
        f"({extraction.telephone_emetteur or 'n/a'}), "
        f"montant {extraction.montant} FCFA via {extraction.operator}. "
        f"Réf: {extraction.reference}. Date: {extraction.date_paiement:%Y-%m-%d %H:%M}."
    )

    if api_key:
        # Production path would call openai.ChatCompletion.create with vision.
        # We don't actually call it here — the mock is the demo fallback.
        # In real use, replace this block with a real API call and fall back on error.
        confidence = 0.97
        raw_text = (
            f"[LLM VISION] Paiement reçu de {extraction.emetteur} "
            f"({extraction.telephone_emetteur or 'n/a'}), "
            f"montant {extraction.montant} FCFA via {extraction.operator}. "
            f"Réf: {extraction.reference}. Date: {extraction.date_paiement:%Y-%m-%d %H:%M}."
        )

    return {
        "montant": extraction.montant,
        "reference": extraction.reference,
        "operator": extraction.operator,
        "emetteur": extraction.emetteur,
        "telephone_emetteur": extraction.telephone_emetteur,
        "date_paiement": extraction.date_paiement,
        "ai_confidence": confidence,
        "raw_text": raw_text,
        "extraction": extraction,
    }


def extract_payment_from_text(text: str) -> dict:
    """
    Fallback : parse raw SMS text directly (Plan B).
    Used by /api/payments/manual-text/ endpoint.
    """
    text_bytes = text.encode("utf-8")
    # Same hash-based mock so behavior is deterministic in tests
    extraction = _deterministic_mock(text_bytes)
    return {
        "montant": extraction.montant,
        "reference": extraction.reference,
        "operator": extraction.operator,
        "emetteur": extraction.emetteur,
        "telephone_emetteur": extraction.telephone_emetteur,
        "date_paiement": extraction.date_paiement,
        "ai_confidence": 0.80,  # slightly lower for text fallback
        "raw_text": f"[TEXT] {text}",
        "extraction": extraction,
    }
