# MoneXa — Application Mobile Flutter

Application mobile MoneXa — CFO virtuel pour PME ouest-africaines.
Réalisé par **D3BUG 0R DI3**.

## Architecture

Clean Architecture + BLoC + Hive (offline-first).

```
lib/
├── main.dart
├── core/
│   ├── constants/      (app_constants.dart)
│   ├── theme/          (app_colors.dart, app_theme.dart)
│   ├── network/        (api_client.dart, api_endpoints.dart)
│   ├── router/         (app_router.dart)
│   └── l10n/           (app_fr.arb, app_ee.arb, app_kab.arb)
├── features/
│   ├── auth/           (login + JWT)
│   ├── dashboard/      (KPIs agrégés)
│   ├── upload_evidence/(capture reçu → IA pipeline)
│   ├── payments/       (liste paiements + filtres)
│   └── profile/        (2FA, langue, déconnexion)
└── shared/
    ├── widgets/        (kpi_card.dart, ...)
    └── utils/          (formatters.dart)
```

## Démarrage

```bash
cd mobile_app
flutter pub get
flutter run
```

## Comptes de test

| Rôle | Email | Mot de passe |
|---|---|---|
| Gérant | gerant@monexa.tg | Monexa2026! |
| Comptable | comptable@monexa.tg | Monexa2026! |
| Caissier | caissier@monexa.tg | Monexa2026! |

## Configuration

L'API par défaut pointe vers `http://10.0.2.2:8000` (Android emulator → localhost du host).
Pour un device physique, override via `--dart-define=API_BASE_URL=http://192.168.x.x:8000`.

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

## Fonctionnalités

- ✅ Authentification JWT (stockée dans flutter_secure_storage)
- ✅ Dashboard KPIs agrégés par canal
- ✅ Capture de reçu via caméra → pipeline IA → matching automatique
- ✅ Liste des paiements (filtre par statut)
- ✅ Profil : 2FA (Gérant), changement de langue (FR / Ewé / Kabyé)
- ✅ Offline-first via cache Hive
