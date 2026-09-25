# Tests

```bash
cd backend
python -m pytest
```

Niveaux :

- Unitaire : matcher, ingest, KPIs, forecast
- API : RBAC, evidence, golden demo
- Sécurité : `accounts/tests/test_tenancy.py` (isolation A vs B + ID direct)

Flutter :

```bash
cd mobile   # ou le dossier Flutter du dépôt
flutter test
```

CI GitHub Actions : lint compileall + pytest + `docker compose build`.
