"""
Tests du chatbot TresorIA.
"""
import pytest


@pytest.mark.django_db
def test_assistant_returns_answer_for_solde_tmoney(gerant_client):
    """TresorIA répond à une question sur le solde T-Money."""
    resp = gerant_client.post("/api/assistant/ask/", {"question": "Combien ai-je en T-Money ?"}, format="json")
    assert resp.status_code == 200
    assert "T-Money" in resp.data["answer"] or "tmoney" in resp.data["answer"].lower()


@pytest.mark.django_db
def test_assistant_returns_answer_for_anomalies(gerant_client):
    """TresorIA répond à une question sur les anomalies."""
    resp = gerant_client.post("/api/assistant/ask/", {"question": "Combien d'anomalies ?"}, format="json")
    assert resp.status_code == 200
    assert "anomalie" in resp.data["answer"].lower()


@pytest.mark.django_db
def test_assistant_fallback_for_unknown_question(gerant_client):
    """TresorIA retourne une réponse fallback pour les questions inconnues."""
    resp = gerant_client.post("/api/assistant/ask/", {"question": "qqqqq xxx zzz"}, format="json")
    assert resp.status_code == 200
    assert "n'ai pas compris" in resp.data["answer"].lower() or "voici ce que" in resp.data["answer"].lower()


@pytest.mark.django_db
def test_assistant_requires_authentication(api_client):
    """L'endpoint /api/assistant/ask/ exige une authentification."""
    resp = api_client.post("/api/assistant/ask/", {"question": "test"}, format="json")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_assistant_validates_question_length(gerant_client):
    """L'endpoint valide la longueur de la question."""
    resp = gerant_client.post("/api/assistant/ask/", {"question": "ab"}, format="json")
    assert resp.status_code == 400
