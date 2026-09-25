import 'package:intl/intl.dart';

class Formatters {
  Formatters._();

  /// Formate un montant en Francs CFA : 350000 -> "350 000 FCFA"
  static String formatFcfa(dynamic amount) {
    if (amount == null) return "0 FCFA";
    double val = 0.0;
    if (amount is num) {
      val = amount.toDouble();
    } else if (amount is String) {
      val = double.tryParse(amount) ?? 0.0;
    }

    final formatter = NumberFormat('#,##0', 'fr_FR');
    final formatted = formatter.format(val).replaceAll(RegExp(r'[\s\u00a0\u202f,]+'), ' ');
    return "$formatted FCFA";
  }

  /// Formate une date ISO : "2026-09-25T12:00:00Z" -> "25 sept. 2026 12:00"
  static String formatDateTime(dynamic dateStr) {
    if (dateStr == null) return "—";
    DateTime? dt;
    if (dateStr is DateTime) {
      dt = dateStr;
    } else if (dateStr is String) {
      dt = DateTime.tryParse(dateStr);
    }
    if (dt == null) return dateStr.toString();

    final local = dt.toLocal();
    final formatter = DateFormat("d MMM y 'à' HH:mm", 'fr_FR');
    return formatter.format(local);
  }

  /// Formate une date courte : "25/09/2026"
  static String formatShortDate(dynamic dateStr) {
    if (dateStr == null) return "—";
    DateTime? dt;
    if (dateStr is DateTime) {
      dt = dateStr;
    } else if (dateStr is String) {
      dt = DateTime.tryParse(dateStr);
    }
    if (dt == null) return dateStr.toString();

    final formatter = DateFormat('dd/MM/yyyy', 'fr_FR');
    return formatter.format(dt);
  }
}
