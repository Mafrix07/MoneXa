# Déploiement MoneXa

## Option 1 — Docker Compose (recommandé pour démo)

```bash
# Clone du repo
git clone https://github.com/Mafrix07/DEBUG.git monexa
cd monexa

# Configurer les variables d'environnement
cp backend/.env.example backend/.env
# Éditer backend/.env avec une SECRET_KEY aléatoire et DEBUG=False pour la prod

# Lancer les conteneurs (Backend Django + PostgreSQL)
docker-compose up --build -d

# Initialiser la base de données et les données de démo
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py seed_demo
```

Accès :
- Backend API : http://localhost:8000
- Swagger UI : http://localhost:8000/api/schema/swagger-ui/
- Django Admin : http://localhost:8000/admin/

## Option 2 — Backend local (Python)

```bash
cd backend

# Créer un venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Pour SQLite (tests), laisser DATABASE_URL vide
# Pour PostgreSQL, DATABASE_URL=postgres://user:pass@localhost:5432/monexa

# Appliquer les migrations
python manage.py migrate

# Charger les données de démonstration
python manage.py seed_demo

# Pré-calculer les prévisions Holt-Winters
python manage.py generate_forecast

# Lancer le serveur
python manage.py runserver 0.0.0.0:8000
```

## Option 3 — App mobile Flutter

```bash
cd mobile_app

# Installer les dépendances
flutter pub get

# Lancer sur un émulateur Android ou device physique
flutter run

# Pour pointer vers une API différente :
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

## Production — Render / Railway

Le backend est déployable sur Render ou Railway :

1. Créer un service Web Python pointant vers `backend/`
2. Build command : `pip install -r requirements.txt`
3. Start command : `gunicorn monexa_config.wsgi:application --bind 0.0.0.0:$PORT`
4. Add Postgres add-on (Render/Railway gère l'URL automatiquement dans `DATABASE_URL`)
5. Variables d'environnement :
   - `SECRET_KEY` (aléatoire)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=*`
   - `DATABASE_URL` (auto-fourni par le add-on)
   - `CORS_ALLOWED_ORIGINS=https://monexa-app.vercel.app`
6. Post-deploy : `python manage.py migrate && python manage.py seed_demo`

## Vérifications post-déploiement

```bash
# Backend health check
curl https://your-app.onrender.com/api/schema/swagger-ui/  # doit afficher Swagger UI

# Auth test
curl -X POST https://your-app.onrender.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "gerant@monexa.tg", "password": "Monexa2026!"}'

# Dashboard
curl https://your-app.onrender.com/api/dashboard/summary/ \
  -H "Authorization: Bearer <token>"

# Audit immuable — vérifier la chaîne
python manage.py shell -c "from auditing.services import verify_chain; print(verify_chain())"
```

## Plan B de démo (cahier des charges §16.3)

Si la démo live échoue :
1. Vidéo de secours 60s
2. Django Admin en back-office hors-ligne
3. seed_demo Docker local sur portable
