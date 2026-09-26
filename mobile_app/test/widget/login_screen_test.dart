import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:monexa/core/constants/app_constants.dart';
import 'package:monexa/features/auth/data/auth_repository.dart';
import 'package:monexa/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:monexa/features/auth/presentation/screens/login_screen.dart';

class MockAuthRepository extends AuthRepository {
  @override
  Future<UserModel?> getStoredUser() async => null;
}

void main() {
  testWidgets('LoginScreen renders brand, inputs, and demo chips correctly', (tester) async {
    final authBloc = AuthBloc(repository: MockAuthRepository());

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider<AuthBloc>.value(
          value: authBloc,
          child: const LoginScreen(),
        ),
      ),
    );

    expect(find.text('MONEXA'), findsOneWidget);
    expect(find.text('Connexion'), findsOneWidget);
    expect(find.text('Se connecter'), findsOneWidget);

    expect(find.text('Laura'), findsOneWidget);
    expect(find.text('Djamie'), findsOneWidget);
    expect(find.text('Judy'), findsOneWidget);

    await tester.tap(find.text('Judy'));
    await tester.pump();

    expect(find.text('judy@judyspices.tg'), findsOneWidget);

    await authBloc.close();
  });
}
