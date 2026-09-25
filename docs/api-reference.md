# Documentation de l'API MoneXa

## Endpoints

| Méthode | Route | Rôle min. | Description |
|---|---|---|---|
| `POST` | `/api/auth/token/` | public | JWT login (access + refresh) |
| `POST` | `/api/auth/refresh/` | public | Renouvellement du token |
| `GET` | `/api/auth/me/` | connecté | Profil utilisateur + rôle |
| `PATCH` | `/api/auth/me/2fa/` | gérant | Toggle 2FA TOTP |
| `GET/POST` | `/api/invoices/` | caissier+ | CRUD factures (num. auto) |
| `GET/PATCH` | `/api/invoices/{id}/` | comptable+ | Détail / validation facture |
| `POST` | `/api/evidence/` | caissier+ | Preuve unifiée (image, sms, csv, manual) |
| `GET` | `/api/payments/{id}/explain/` | caissier+ | Critères réels du rapprochement |
| `PATCH` | `/api/payments/{id}/review/` | comptable+ | HITL ACCEPT / REJECT / ATTACH |
| `GET/POST` | `/api/sources/` | comptable+ / gérant | Sources financières (connecteurs **simulés**) |
| `POST` | `/api/sources/{id}/sync/` | gérant | Sync idempotente |
| `GET` | `/api/sources/{id}/health/` | comptable+ | Santé du connecteur |
| `POST` | `/api/payments/manual-text/` | caissier+ | Fallback : texte SMS collé |
| `GET` | `/api/payments/?status=A_VALIDER` | comptable+ | File de validation |
| `PATCH` | `/api/payments/{id}/validate/` | comptable+ | Validation / rejet paiement |
| `GET` | `/api/accounts/` | comptable+ | Comptes + soldes agrégés |
| `GET` | `/api/dashboard/summary/` | connecté | KPIs + répartition par canal |
| `GET` | `/api/reports/forecast/?days=30` | comptable+ | Prévision trésorerie J+7 / J+30 |
| `GET` | `/api/anomalies/` | gérant | File d'anomalies (règles + Isolation Forest) |
| `GET` | `/api/audit-logs/` | gérant | Journal immuable (lecture seule) |
| `POST` | `/api/assistant/ask/` | connecté | Chatbot TresorIA (10 req/min) |
| `GET` | `/api/reports/export/?format=csv&model=payments` | comptable+ | Export CSV / Excel / SYSCOHADA |
| `GET` | `/api/schema/` | — | Schéma OpenAPI 3 |
| `GET` | `/api/schema/swagger-ui/` | — | Swagger UI interactif |
| `GET` | `/api/schema/redoc/` | — | Redoc UI |

## Exemples

### Login

```bash
POST /api/auth/token/
{
  "email": "gerant@monexa.tg",
  "password": "Monexa2026!"
}
→ 200
{
  "access": "eyJhbGc...",
  "refresh": "eyJhbGc..."
}
```

### Upload d'un reçu Mobile Money

```bash
POST /api/payments/evidence/
Content-Type: multipart/form-data
Authorization: Bearer eyJ...
Body: image=@recu.jpg

→ 201
{
  "id": 242,
  "provider_ref": "TMX8847291023",
  "amount": "750000.00",
  "channel": "TMONEY",
  "payer_name": "Kossi Mensah",
  "payer_phone": "+228 90 12 34 56",
  "paid_at": "2026-09-24T14:23:00Z",
  "status": "A_VALIDER",
  "match_method": "AUTO_MONTANT",
  "ai_confidence": 0.97,
  "raw_text": "[LLM VISION] Paiement reçu de Kossi Mensah...",
  "invoice": 47,
  "anomaly_score": 0.12
}
```

### Demander à TresorIA

```bash
POST /api/assistant/ask/
Authorization: Bearer eyJ...
{
  "question": "Combien ai-je en T-Money ?"
}

→ 200
{
  "answer": "Votre solde T-Money actuel est de 5 240 000 FCFA. C'est le canal qui représente la part la plus importante de votre trésorerie mobile.",
  "question": "Combien ai-je en T-Money ?"
}
```

### Prévisions Holt-Winters

```bash
GET /api/reports/forecast/?days=30
Authorization: Bearer eyJ...

→ 200
{
  "days": 30,
  "historical": [{"date": "2026-07-01", "net": 125000.0}, ...],
  "forecast": [130000.0, 142000.0, ...],
  "confidence_low": [110000.0, 120000.0, ...],
  "confidence_high": [150000.0, 164000.0, ...],
  "cumulative_forecast": 4250000.0,
  "model": "Holt-Winters (triple exponential smoothing, additive)"
}
```

### Journal d'audit immuable

```bash
GET /api/audit-logs/
Authorization: Bearer eyJ...

→ 200
[
  {
    "id": 250,
    "user": 3,
    "user_email": "caissier@monexa.tg",
    "action": "PAYMENT_CREATED",
    "entity": "Payment",
    "entity_id": "200",
    "details": {"provider_ref": "TMX...", "amount": 750000.0, ...},
    "timestamp": "2026-09-24T15:08:42Z",
    "prev_hash": "a3f5c8d9...",
    "hash": "b4e6d9e0...",
    "hash_short": "b4e6d9e0f1a2b3c4…"
  }
]
```
