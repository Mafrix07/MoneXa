"""
Tests du pipeline IA (extraction LLM multimodale — mock).
"""
import pytest
from finance.services.ai_pipeline import (
    extract_payment_from_image, extract_payment_from_text,
    PaymentExtraction,
)


def test_extraction_returns_valid_schema():
    """L'extraction d'une image mock retourne un PaymentExtraction valide."""
    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    result = extract_payment_from_image(fake_bytes, "test.png")
    assert "extraction" in result
    assert isinstance(result["extraction"], PaymentExtraction)
    assert result["montant"] > 0
    assert result["operator"] in ("TMONEY", "MOOV", "FLOOZ")
    assert 0 <= result["ai_confidence"] <= 1


def test_extraction_is_deterministic():
    """La même image donne toujours le même résultat (mock déterministe)."""
    fake_bytes = b"identical content" * 5
    r1 = extract_payment_from_image(fake_bytes, "a.png")
    r2 = extract_payment_from_image(fake_bytes, "b.png")
    assert r1["montant"] == r2["montant"]
    assert r1["reference"] == r2["reference"]
    assert r1["operator"] == r2["operator"]


def test_extraction_different_images_give_different_results():
    """Deux images différentes donnent deux résultats différents."""
    r1 = extract_payment_from_image(b"content A", "a.png")
    r2 = extract_payment_from_image(b"content B", "b.png")
    # At least one field should differ (statistically very likely)
    assert (r1["montant"] != r2["montant"] or r1["reference"] != r2["reference"])


def test_text_fallback_works():
    """Le fallback texte (Plan B) fonctionne."""
    result = extract_payment_from_text("Paiement recu: 50000 FCFA de Kossi. Ref: TMX1234567890.")
    assert "montant" in result
    assert "raw_text" in result
    assert "TMX" in result["raw_text"] or "Paiement" in result["raw_text"]


def test_payment_extraction_schema_rejects_negative_amount():
    """Pydantic rejette un montant négatif."""
    from pydantic import ValidationError
    from decimal import Decimal
    from datetime import datetime, timezone

    with pytest.raises(ValidationError):
        PaymentExtraction(
            montant=Decimal("-100"),
            reference="REF",
            operator="TMONEY",
            emetteur="Kossi",
            date_paiement=datetime.now(timezone.utc),
        )


def test_payment_extraction_schema_rejects_unknown_operator():
    """Pydantic rejette un opérateur inconnu."""
    from pydantic import ValidationError
    from decimal import Decimal
    from datetime import datetime, timezone

    with pytest.raises(ValidationError):
        PaymentExtraction(
            montant=Decimal("100"),
            reference="REF",
            operator="UNKNOWN_OPERATOR",
            emetteur="Kossi",
            date_paiement=datetime.now(timezone.utc),
        )
