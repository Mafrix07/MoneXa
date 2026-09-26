import 'package:flutter/foundation.dart';

/// Constantes globales de l'application MoneXa
class AppConstants {
  AppConstants._();

  static const String _apiFromEnv = String.fromEnvironment('API_BASE_URL');

  /// Android emulator → 10.0.2.2 ; web / desktop → localhost.
  static String get defaultApiUrl {
    if (_apiFromEnv.isNotEmpty) return _apiFromEnv;
    return kIsWeb ? 'http://127.0.0.1:8000' : 'http://10.0.2.2:8000';
  }

  // Clés de stockage sécurisé (flutter_secure_storage)
  static const String tokenKey = 'monexa_access_token';
  static const String refreshTokenKey = 'monexa_refresh_token';
  static const String userEmailKey = 'monexa_user_email';
  static const String userRoleKey = 'monexa_user_role';
  static const String userNameKey = 'monexa_user_name';
  static const String userLanguageKey = 'monexa_user_lang';

  // Noms des boîtes Hive pour le cache Offline-First
  static const String kpiBoxName = 'monexa_kpis_cache';
  static const String paymentsBoxName = 'monexa_payments_cache';
  static const String offlineQueueBoxName = 'monexa_offline_queue';

  // Langues supportées
  static const String langFr = 'fr';
  static const String langEe = 'ee'; // Ewé
  static const String langKab = 'kab'; // Kabyé

  // Rôles RBAC
  static const String roleGerant = 'GERANT';
  static const String roleComptable = 'COMPTABLE';
  static const String roleCaissier = 'CAISSIER';

  static const String logoAsset = 'assets/images/monexa_logo.png';
}
