import 'package:flutter_test/flutter_test.dart';
import 'package:monexa/core/constants/app_constants.dart';
import 'package:monexa/features/auth/data/auth_repository.dart';
import 'package:monexa/features/auth/presentation/bloc/auth_bloc.dart';

class FakeAuthRepository extends AuthRepository {
  UserModel? mockUser;
  bool shouldFail = false;

  @override
  Future<UserModel> login({required String email, required String password}) async {
    if (shouldFail) {
      throw Exception('Identifiants invalides');
    }
    return mockUser ??
        UserModel(
          id: 1,
          email: email,
          role: AppConstants.roleCaissier,
          displayName: 'Test User',
        );
  }

  @override
  Future<UserModel?> getStoredUser() async {
    return mockUser;
  }

  @override
  Future<void> logout() async {
    mockUser = null;
  }
}

void main() {
  group('AuthBloc tests', () {
    late FakeAuthRepository fakeRepo;
    late AuthBloc authBloc;

    setUp(() {
      fakeRepo = FakeAuthRepository();
      authBloc = AuthBloc(repository: fakeRepo);
    });

    tearDown(() {
      authBloc.close();
    });

    test('Initial state is AuthInitial', () {
      expect(authBloc.state, isA<AuthInitial>());
    });

    test('CheckAuthStatusEvent emits Unauthenticated when no stored user', () async {
      fakeRepo.mockUser = null;
      authBloc.add(CheckAuthStatusEvent());

      await expectLater(
        authBloc.stream,
        emitsInOrder([
          isA<AuthLoading>(),
          isA<Unauthenticated>(),
        ]),
      );
    });

    test('LoginSubmittedEvent emits AuthLoading then Authenticated on success', () async {
      authBloc.add(LoginSubmittedEvent(email: 'caissier@monexa.tg', password: 'password'));

      await expectLater(
        authBloc.stream,
        emitsInOrder([
          isA<AuthLoading>(),
          predicate<AuthState>((state) {
            return state is Authenticated && state.user.email == 'caissier@monexa.tg';
          }),
        ]),
      );
    });

    test('LoginSubmittedEvent emits AuthLoading then AuthFailure on error', () async {
      fakeRepo.shouldFail = true;
      authBloc.add(LoginSubmittedEvent(email: 'wrong@monexa.tg', password: 'wrong'));

      await expectLater(
        authBloc.stream,
        emitsInOrder([
          isA<AuthLoading>(),
          predicate<AuthState>((state) {
            return state is AuthFailure && state.message.contains('Identifiants invalides');
          }),
        ]),
      );
    });

    test('LogoutRequestedEvent clears session and emits Unauthenticated', () async {
      authBloc.add(LogoutRequestedEvent());

      await expectLater(
        authBloc.stream,
        emitsInOrder([
          isA<AuthLoading>(),
          isA<Unauthenticated>(),
        ]),
      );
    });
  });
}
