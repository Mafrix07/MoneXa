# Sécurité

MONEXA traite des données financières. Le backend est la source d'autorité : le mobile ne fait jamais confiance à lui-même pour le RBAC.

## Contrôles en place

- Mots de passe hashés (Django PBKDF2)
- JWT courte durée + refresh rotatif + blacklist
- RBAC (Gérant / Comptable / Caissier) sur chaque viewset
- Isolation multi-tenant sur querysets, exports, KPIs, assistant
- Rate limiting DRF (anon / user / TresorIA)
- CORS listé (pas `*` en production si `DEBUG=False`)
- `SECRET_KEY` par défaut refusée si `DEBUG=False`
- `ALLOWED_HOSTS=*` interdit si `DEBUG=False`
- Preuves : `ImageField` sous `MEDIA_ROOT` (local). En production, brancher un stockage objet (S3 compatible) — pas le disque du conteneur comme unique copie
- Journal d'audit hashé SHA-256 (immuable applicativement)
- En-tête `X-Request-ID`

## Secrets

Aucun secret réel dans Git. Copier `backend/.env.example`. Clés OpenAI / Gemini / connecteurs uniquement via l'environnement.

Les connecteurs opérateurs sont **simulés** tant qu'aucun credential officiel n'est fourni. Ils ne se font pas passer pour une API réelle.

## Sauvegardes

Voir `docs/deployment.md`. Un backup n'est fiable qu'après un exercice de restauration.
