# Connecteurs

Abstraction : `finance/connectors/` (`connect`, `fetch_transactions`, `sync`).

| Connecteur | Mode actuel | Notes |
|---|---|---|
| T-Money / Moov / Flooz | SIMULATED | Aucune API opérateur officielle branchée |
| Banque | IMPORT (CSV) | Prêt pour un adaptateur Open Banking ultérieur |
| CSV / Excel | IMPORT | Pipeline validation → normalisation → déduplication → ledger |
| SMS | IMPORT | Parser déterministe + IA optionnelle |
| Manuel | MANUAL | Saisie humaine |

Idempotence : `provider_ref` unique **par organisation**. Une seconde sync ignore les doublons.

Erreurs attendues (timeout, token, pagination) : statut de source `ERROR` + `last_error`, sans planter l'API.
