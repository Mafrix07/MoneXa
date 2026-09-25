# Dépannage

| Symptôme | Piste |
|---|---|
| `ImproperlyConfigured SECRET_KEY` | `DEBUG=False` avec une clé d'exemple. Générer un secret long. |
| `/ready/` 503 | PostgreSQL down ou `DATABASE_URL` incorrect |
| Extraction photo échoue | Pas de clé IA : saisir le SMS / le texte. L'app ne doit pas crasher. |
| Doublon 409 | Référence opérateur déjà dans l'organisation |
| Liste vide après login | Utilisateur sans `organization` (sauf superuser) |
| Port 5432 déjà pris | Compose bind `127.0.0.1:5432` uniquement |

Logs : préfixe `[asctime] LEVEL name`. Corrélation : en-tête `X-Request-ID`.
