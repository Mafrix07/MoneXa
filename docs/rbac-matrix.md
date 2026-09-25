# Matrice RBAC MoneXa

## Hiérarchie des rôles

**GERANT > COMPTABLE > CAISSIER**

## Permissions détaillées

| Action | Caissier | Comptable | Gérant |
|---|:---:|:---:|:---:|
| Créer une facture | ✓ | ✓ | ✓ |
| Uploader une preuve de paiement | ✓ | ✓ | ✓ |
| Consulter ses paiements | ✓ (les siens) | ✓ (tous) | ✓ (tous) |
| Valider un paiement A_VALIDER | — | ✓ | ✓ |
| Exporter rapports (Excel/PDF) | — | ✓ | ✓ |
| Résoudre une anomalie | — | — | ✓ |
| Consulter le journal d'audit | — | — | ✓ |
| Gérer les utilisateurs | — | — | ✓ |
| Accès Django Admin | — | ✓ (lecture) | ✓ (full + 2FA) |

## Comptes de test

| Rôle | Email | Mot de passe |
|---|---|---|
| Gérant | `gerant@monexa.tg` | `Monexa2026!` |
| Comptable | `comptable@monexa.tg` | `Monexa2026!` |
| Caissier | `caissier@monexa.tg` | `Monexa2026!` |

## Endpoints API par rôle

| Endpoint | Rôle minimum |
|---|---|
| `POST /api/auth/token/` | public |
| `GET /api/auth/me/` | connecté |
| `GET/POST /api/invoices/` | caissier+ |
| `GET/PATCH /api/invoices/{id}/` | comptable+ |
| `POST /api/payments/evidence/` | caissier+ |
| `POST /api/payments/manual-text/` | caissier+ |
| `GET /api/payments/?status=A_VALIDER` | comptable+ |
| `PATCH /api/payments/{id}/validate/` | comptable+ |
| `GET /api/accounts/` | comptable+ |
| `GET /api/dashboard/summary/` | connecté |
| `GET /api/reports/forecast/?days=30` | comptable+ |
| `GET /api/anomalies/` | gérant |
| `GET /api/audit-logs/` | gérant |
| `POST /api/assistant/ask/` | connecté (10 req/min) |
| `GET /api/reports/export/?format=csv` | comptable+ |
