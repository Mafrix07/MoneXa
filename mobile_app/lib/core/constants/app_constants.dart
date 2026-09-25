/// Constantes globales de l'application MoneXa
class AppConstants {
  AppConstants._();

  // URL de l'API Backend Django
  // Par défaut 10.0.2.2:8000 pour émulateur Android, ou via --dart-define=API_BASE_URL=...
  static const String defaultApiUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

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
}
