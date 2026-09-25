# Architecture MoneXa

## Vue d'ensemble

MoneXa suit un monolithe Django modulaire, avec une app mobile Flutter séparée.

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENTS                                   │
│  ┌─────────────────────┐    ┌──────────────────────────────┐   │
│  │  App Mobile Flutter  │    │  Back-office Django Admin    │   │
│  │  (Caissier, Gérant)  │    │  + HTMX (Comptable, Gérant)  │   │
│  │  Offline-first Hive  │    │  i18n FR / Ewé / Kabyé       │   │
│  └──────────┬──────────┘    └─────────────┬────────────────┘   │
└─────────────┼─────────────────────────────┼─────────────────────┘
              │ JWT / HTTPS                  │ Session Auth
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Backend Django 5 + DRF                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  REST API (/api/v1/)                                      │   │
│  │  Auth JWT (simplejwt)  •  RBAC (3 rôles)  •  Throttling  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Services IA Internes (finance/services/)                 │   │
│  │  • ai_pipeline  — LLM multimodal (GPT-4o-mini Vision)     │   │
│  │  • matcher      — Cascade réconciliation (4 niveaux)      │   │
│  │  • anomalies    — Règles + Isolation Forest               │   │
│  │  • forecast     — Holt-Winters (lissage triple)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Audit SHA-256 (save/delete Python ; pas de trigger PG)   │   │
│  │  Toute altération applicative brise la chaîne.            │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
                   ┌──────────────────────┐
                   │   PostgreSQL 16      │
                   │  ACID (pas de trigger d'audit dans ce proto) │
                   └──────────────────────┘
```

## Flux principal de données

1. Le caissier saisit une facture ou photographie un reçu Mobile Money depuis l'app Flutter.
2. L'image est envoyée à `POST /api/payments/evidence/` du backend Django.
3. Le pipeline IA interne (`ai_pipeline.py`) extrait les données via un LLM multimodal, valide le JSON via Pydantic, crée un objet `Payment` avec `raw_text` et `ai_confidence`, et le soumet au matcher.
4. Le matcher (`matcher.py`) exécute la cascade de réconciliation (référence exacte → montant + 7 jours → fuzzy nom/téléphone → A_VALIDER) et met à jour le statut.
5. Les données sont stockées dans PostgreSQL, une entrée d'audit est créée via signal `post_save`, et le comptable est notifié.
6. Le caissier et le comptable consultent le dashboard depuis respectivement l'app mobile et le back-office web.

## Applications Django

| App | Responsabilité |
|---|---|
| `accounts` | Custom User, RBAC, JWT, 2FA |
| `finance` | Account, Invoice, Payment, Expense + services IA |
| `auditing` | AuditLog immuable (hash-chainé SHA-256) |
| `reporting` | KPIs dashboard, exports CSV/Excel, prévisions |
| `assistant` | TresorIA chatbot (KPIs pré-calculés, jamais de SQL) |

## Sécurité

- **3 règles d'or financières** :
  1. Pas de FloatField pour l'argent → `DecimalField(14, 2)`
  2. Contrainte DB `unique=True` sur `provider_ref` (anti-doublon natif)
  3. Toute écriture dans `transaction.atomic()`
- **RBAC** : 3 rôles (Gérant > Comptable > Caissier)
- **Multi-tenant** : `Organization` isole toutes les données métier (querysets, exports, KPIs, TresorIA, audit). Unicité `provider_ref` et `invoice.reference` **par organisation**.
- **Audit immuable** : hash-chainage SHA-256, `save()` et `delete()` lèvent `PermissionError` (chaîne Python, pas de trigger PostgreSQL)
- **Connecteurs** : T-Money / Moov / Flooz / banque sont **simulés**. L'architecture (`finance/connectors/`) permet de les remplacer par de vraies API plus tard.
- **2FA TOTP** optionnel pour le Gérant (`django-otp`)
- **JWT** : access 15min, refresh 7j, rotation avec blacklist
- **CORS** strict, **throttling** 60/min global + 10/min pour TresorIA
- **Santé** : `GET /health/` (liveness), `GET /ready/` (base joignable)

## Multi-tenant

Une entreprise = une `Organization`. Les utilisateurs, comptes, factures, paiements, dépenses, sources, prévisions et journaux d'audit portent un FK `organization`. Les querysets API filtrent toujours sur l'organisation de l'utilisateur authentifié (sauf superuser sans org). `POST /api/auth/register/` crée l'organisation et le gérant fondateur. `seed_demo` reste un outil de développement, jamais le chemin de production.
