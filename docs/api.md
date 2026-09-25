# API

Préfixe actuel : `/api/` (pas de rupture `/api/v1/` tant qu'une migration de clients n'est pas planifiée).

Auth : JWT `POST /api/auth/token/`. Onboarding : `POST /api/auth/register/`.

Ressources : `/api/users/`, `/api/accounts/`, `/api/invoices/`, `/api/payments/`, `/api/expenses/`, `/api/sources/`, `/api/evidence/`, `/api/dashboard/summary/`, `/api/reports/forecast/`, `/api/reports/export/`, `/api/anomalies/`, `/api/audit-logs/`, `/api/assistant/ask/`, `/api/organizations/me/`.

Santé : `/health/`, `/ready/`. Schéma OpenAPI : `/api/schema/swagger-ui/`.

Pagination : 20 éléments. Filtres / recherche DRF sur les listes.

Toutes les listes métier sont scopées à l'organisation du jeton.
