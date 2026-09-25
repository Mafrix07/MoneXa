import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/shared/widgets/kpi_card.dart';
import 'package:monexa/shared/widgets/status_badge.dart';

void main() {
  group('UI Components tests', () {
    testWidgets('StatusBadge displays correct label for status and channels', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Column(
              children: [
                StatusBadge(status: 'RECONCILIE'),
                StatusBadge(status: 'A_VALIDER'),
                StatusBadge(status: 'TMONEY', isChannel: true),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Réconcilié'), findsOneWidget);
      expect(find.text('À valider'), findsOneWidget);
      expect(find.text('TMONEY'), findsOneWidget);
    });

    testWidgets('KpiCard renders label, value and icon', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: KpiCard(
              label: 'Solde Total',
              value: '4 850 000 FCFA',
              icon: Icons.account_balance_wallet,
              color: AppColors.primary,
            ),
          ),
        ),
      );

      expect(find.text('Solde Total'), findsOneWidget);
      expect(find.text('4 850 000 FCFA'), findsOneWidget);
      expect(find.byIcon(Icons.account_balance_wallet), findsOneWidget);
    });
  });
}
