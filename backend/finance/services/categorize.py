"""
Catégorisation des dépenses — règles métier, puis LLM si clé présente.
"""
from __future__ import annotations

import re

from finance.models import ExpenseCategory
from finance.services.llm import chat_json, llm_configured

_RULES = (
    (ExpenseCategory.LOYER, r"loyer|immo|bail|location|logement"),
    (ExpenseCategory.SALAIRES, r"salaire|paie|cnss|bulletin"),
    (ExpenseCategory.TRANSPORT, r"essence|carburant|taxi|moto|transport|ceet"),
    (ExpenseCategory.FOURNITURES, r"fourniture|papeterie|encre|papier"),
    (ExpenseCategory.FOURNISSEURS, r"fournisseur|stock|marchandise|achat"),
)


def categorize_expense(supplier: str, note: str = "", current: str = "") -> str:
    if current and current != ExpenseCategory.AUTRE:
        return current
    blob = f"{supplier} {note}".lower()
    for cat, pat in _RULES:
        if re.search(pat, blob, re.I):
            return cat

    if not llm_configured():
        return current or ExpenseCategory.AUTRE

    try:
        data = chat_json(
            system=(
                "Classe une dépense PME togolaise. JSON {\"category\": \"...\"}. "
                "Valeurs autorisées: LOYER, SALAIRES, FOURNISSEURS, TRANSPORT, FOURNITURES, AUTRE. "
                "N'invente pas d'autre valeur."
            ),
            user=f"Fournisseur: {supplier}\nNote: {note}",
            timeout=10,
        )
        cat = str(data.get("category", "AUTRE")).upper()
        allowed = {c.value for c in ExpenseCategory}
        return cat if cat in allowed else ExpenseCategory.AUTRE
    except Exception:
        return current or ExpenseCategory.AUTRE
