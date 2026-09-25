# Base de données

Production : PostgreSQL 16. Tests : SQLite si `DATABASE_URL` vide.

Migrations Django uniquement — jamais d'ALTER manuel.

Modèle central (ledger) : `Payment` (encaissements) + `Expense` (décaissements), montants `Decimal(14, 2)`.

Contraintes :

- `(organization, provider_ref)` unique
- `(organization, invoice.reference)` unique
- `(organization, account.name, channel)` unique

Index : `status+paid_at`, `channel+paid_at`, `organization` via FK.

## Sauvegarde

```bash
docker compose exec db pg_dump -U monexa monexa > backup.sql
```

Restauration (exercice obligatoire avant de déclarer un backup fiable) :

```bash
docker compose exec -T db psql -U monexa monexa < backup.sql
```
