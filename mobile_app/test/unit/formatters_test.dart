import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:monexa/shared/utils/formatters.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('fr_FR', null);
  });

  group('Formatters tests', () {
    test('formatFcfa formats numerical amounts properly', () {
      expect(Formatters.formatFcfa(50000), '50 000 FCFA');
      expect(Formatters.formatFcfa(1450000), '1 450 000 FCFA');
      expect(Formatters.formatFcfa(0), '0 FCFA');
      expect(Formatters.formatFcfa(null), '0 FCFA');
      expect(Formatters.formatFcfa('125000'), '125 000 FCFA');
    });

    test('formatShortDate formats dates properly', () {
      expect(Formatters.formatShortDate(null), '—');
      final date = DateTime(2026, 9, 25);
      expect(Formatters.formatShortDate(date), '25/09/2026');
      expect(Formatters.formatShortDate('2026-09-25T14:30:00Z'), '25/09/2026');
    });
  });
}
