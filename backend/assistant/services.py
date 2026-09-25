"""
TresorIA — CFO virtuel en langage naturel.

RÈGLE FONDAMENTALE (cahier des charges §12.1):
- Le LLM ne génère JAMAIS de SQL.
- Le LLM n'a JAMAIS accès à la base.
- Le backend pré-calcule 15 KPIs et les injecte dans le contexte.
- Le LLM ne fait que reformuler les KPIs en langage naturel.

Ici, en mode démo (pas de clé OpenAI), on simule le LLM via un moteur
de règles qui pattern-matche la question et répond avec les KPIs.
"""
from __future__ import annotations
import re
from typing import Optional

from reporting.services import compute_kpis


def _format_fcfa(amount: float) -> str:
    """Format a number as FCFA: '1 250 000 FCFA'."""
    try:
        return f"{int(amount):,} FCFA".replace(",", " ")
    except (ValueError, TypeError):
        return "—"


def answer_question(user, question: str) -> str:
    """
    Generate an answer from the TresorIA chatbot.

    Args:
        user: the authenticated User
        question: the question in natural language (FR)

    Returns:
        A natural-language answer string.
    """
    if not question or len(question.strip()) < 3:
        return (
            "Je n'ai pas bien compris votre question. "
            "Essayez : \"Combien ai-je en T-Money ?\", "
            "\"Quelle est ma trésorerie à 30 jours ?\", "
            "\"Combien d'anomalies ?\" ou "
            "\"Quelles factures sont en retard ?\"."
        )

    q = question.lower().strip()
    kpis = compute_kpis()

    # ── Pattern matching ────────────────────────────────────────────

    # Solde T-Money
    if re.search(r"(tmoney|t-money|t money)", q) and re.search(r"(solde|combien|montant)", q):
        solde = kpis["solde_par_canal"].get("TMONEY", 0)
        return (
            f"Votre solde T-Money actuel est de {_format_fcfa(solde)}. "
            f"C'est le canal qui représente la part la plus importante de votre trésorerie mobile."
        )

    # Solde Moov
    if re.search(r"(moov)", q) and re.search(r"(solde|combien|montant)", q):
        solde = kpis["solde_par_canal"].get("MOOV", 0)
        return f"Votre solde Moov Money actuel est de {_format_fcfa(solde)}."

    # Solde Flooz
    if re.search(r"(flooz)", q) and re.search(r"(solde|combien|montant)", q):
        solde = kpis["solde_par_canal"].get("FLOOZ", 0)
        return f"Votre solde Flooz actuel est de {_format_fcfa(solde)}."

    # Solde total
    if re.search(r"(solde total|combien.*total|trésorerie.*actuelle|tous.*canaux)", q):
        return (
            f"Votre trésorerie totale consolidée est de {_format_fcfa(kpis['solde_total'])}, "
            f"répartie sur tous vos canaux Mobile Money et bancaires."
        )

    # Encaissé 7j / semaine
    if re.search(r"(encaissé|encaisse|recette).*semaine|semaine.*(encaissé|encaisse|recette)", q) \
       or re.search(r"(7.*jour|cette semaine)", q):
        tmoney_share = kpis["solde_par_canal"].get("TMONEY", 0)
        total_solde = kpis["solde_total"] or 1
        tmoney_part = (tmoney_share / total_solde) * 100 if total_solde > 0 else 0
        return (
            f"Cette semaine (7 derniers jours), vous avez encaissé {_format_fcfa(kpis['encaisse_7j'])}. "
            f"Le canal T-Money représente {tmoney_part:.1f}% de votre trésorerie globale."
        )

    # Encaissé 30j / mois
    if re.search(r"(encaissé|encaisse|recette).*(mois|30.*jour)|mois.*(encaissé|encaisse)", q) \
       or re.search(r"30.*jour", q) and "enca" in q:
        return (
            f"Sur les 30 derniers jours, vous avez encaissé {_format_fcfa(kpis['encaisse_30j'])} "
            f"et décaissé {_format_fcfa(kpis['decaisse_30j'])}, "
            f"soit un flux net de {_format_fcfa(kpis['flux_net_30j'])}."
        )

    # Prévisions / trésorerie 30 jours
    if re.search(r"(prévision|prevision|trésorerie.*30|j\+30|projection|future|avenir)", q):
        return (
            f"À J+30, votre trésorerie projetée est de {_format_fcfa(kpis['prevision_j30'])} "
            f"(modèle Holt-Winters, lissage exponentiel triple). "
            f"La prévision à court terme (J+7) est de {_format_fcfa(kpis['prevision_j7'])}."
        )

    # Anomalies
    if re.search(r"(anomalie|fraude|doublon|écart|probleme|problème)", q):
        return (
            f"Vous avez {kpis['nb_anomalies']} anomalie(s) en cours. "
            f"Pour les consulter en détail, accédez à la section Anomalies (réservée au Gérant). "
            f"Les paiements en anomalie nécessitent une résolution manuelle."
        )

    # Factures en retard
    if re.search(r"(facture.*retard|retard.*facture|impayée|impayee|en retard)", q):
        return (
            f"{kpis['factures_en_retard']} facture(s) sont en retard de paiement. "
            f"Vous avez {kpis['factures_en_attente']} facture(s) en attente au total. "
            f"Pensez à relancer les clients avec des factures en retard."
        )

    # Top 5 clients
    if re.search(r"(top.*client|meilleur.*client|client.*fidèle|fidele)", q):
        if kpis["top_5_clients"]:
            lines = []
            for i, c in enumerate(kpis["top_5_clients"][:5], 1):
                lines.append(f"{i}. {c['name']} — {_format_fcfa(c['total'])} sur {c['count']} paiement(s)")
            return "Vos 5 meilleurs clients sont :\n" + "\n".join(lines)
        return "Aucun paiement n'a encore été enregistré."

    # Paiements à valider
    if re.search(r"(valider|à valider|a valider|file.*validation|en attente.*paiement)", q):
        return (
            f"{kpis['paiements_a_valider']} paiement(s) sont en attente de validation "
            f"par le comptable. Connectez-vous avec un compte Comptable ou Gérant pour les valider."
        )

    # Bonjour / hello
    if re.search(r"^(bonjour|salut|hello|bonsoir|coucou)", q):
        return (
            f"Bonjour {user.display_name if user else ''} ! Je suis TresorIA, votre assistant CFO. "
            f"Posez-moi une question sur votre trésorerie : "
            f"\"Solde T-Money\", \"Prévision 30 jours\", \"Anomalies\", \"Factures en retard\"."
        )

    # Fallback
    return (
        "Je n'ai pas compris votre question. Voici ce que je peux faire :\n"
        "• \"Combien ai-je en T-Money ?\" — solde par canal\n"
        "• \"Prévision 30 jours\" — trésorerie projetée\n"
        "• \"Combien d'anomalies ?\" — alertes en cours\n"
        "• \"Factures en retard\" — impayés à relancer\n"
        "• \"Top 5 clients\" — meilleurs payeurs"
    )
