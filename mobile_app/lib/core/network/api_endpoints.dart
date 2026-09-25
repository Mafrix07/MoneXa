/// Endpoints de l'API REST MoneXa (selon cahier des charges §15)
class ApiEndpoints {
  ApiEndpoints._();

  // Auth
  static const String token = '/api/auth/token/';
  static const String refreshToken = '/api/auth/refresh/';
  static const String verifyToken = '/api/auth/verify/';
  static const String me = '/api/auth/me/';
  static const String toggle2FA = '/api/auth/me/2fa/';

  // Reporting & Dashboard
  static const String dashboardSummary = '/api/dashboard/summary/';
  static const String forecast = '/api/reports/forecast/';
  static const String exportReports = '/api/reports/export/';
  static const String anomalies = '/api/anomalies/';
  static const String auditLogs = '/api/audit-logs/';

  // Finance & Transactions
  static const String invoices = '/api/invoices/';
  static const String payments = '/api/payments/';
  static const String paymentEvidence = '/api/payments/evidence/';
  static const String paymentManualText = '/api/payments/manual-text/';
  static String validatePayment(int id) => '/api/payments/$id/validate/';

  static const String accounts = '/api/accounts/';
  static const String expenses = '/api/expenses/';

  // Chatbot TresorIA
  static const String assistantAsk = '/api/assistant/ask/';
}
