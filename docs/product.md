# Produit

MONEXA — intelligence de trésorerie pour flux d'argent fragmentés.

Connecter → Collecter → Normaliser → Réconcilier → Contrôler → Prévoir → Décider.

Chaîne métier : comptes (Mobile Money, banque, caisse) → preuves / imports → ledger (`Payment` / `Expense`) → matching → anomalies (signal, pas « fraude confirmée ») → forecast Holt-Winters si historique suffisant → TresorIA (KPIs structurés, jamais de SQL inventé par le LLM).

L'IA n'est pas obligatoire pour facturer, payer, rapprocher de façon déterministe ou auditer.

Onboarding : `POST /api/auth/register/` crée l'entreprise et le gérant. Les seeds sont des outils de démo.
