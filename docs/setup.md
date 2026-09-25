# Installation locale

## Prérequis

- Python 3.11 ou 3.12
- PostgreSQL 16 (production) — SQLite accepté pour tests
- Flutter 3.22+ pour l'app mobile

## Backend

```bash
cd backend
python -m venv .venv
# Windows : .\.venv\Scripts\activate
# Unix    : source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Unix
python manage.py migrate
python manage.py runserver
```

Ne lancez `seed_demo` / `seed_golden_demo` que pour une démo. Une instance production démarre **vide**.

Onboarding réel : `POST /api/auth/register/` avec `organization_name`, email, mot de passe.

Vérification :

- http://127.0.0.1:8000/health/
- http://127.0.0.1:8000/ready/
- http://127.0.0.1:8000/api/schema/swagger-ui/

## Docker

```bash
docker compose up --build
```

PostgreSQL n'écoute que sur `127.0.0.1:5432`. Pour une base de démo :

```bash
# Unix / Git Bash
RUN_SEED_DEMO=1 docker compose up --build
```

## Flutter

Configurer l'URL API (émulateur : `http://10.0.2.2:8000`). Puis `flutter pub get` et `flutter run`.
