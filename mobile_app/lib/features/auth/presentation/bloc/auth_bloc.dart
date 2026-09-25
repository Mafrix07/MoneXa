import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/auth_repository.dart';

// Events
abstract class AuthEvent {}

class CheckAuthStatusEvent extends AuthEvent {}

class LoginSubmittedEvent extends AuthEvent {
  final String email;
  final String password;
  LoginSubmittedEvent({required this.email, required this.password});
}

class LogoutRequestedEvent extends AuthEvent {}

class Toggle2FAEvent extends AuthEvent {}

// States
abstract class AuthState {}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class Authenticated extends AuthState {
  final UserModel user;
  Authenticated(this.user);
}

class Unauthenticated extends AuthState {}

class AuthFailure extends AuthState {
  final String message;
  AuthFailure(this.message);
}

// BLoC
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repository;

  AuthBloc({AuthRepository? repository})
      : _repository = repository ?? AuthRepository(),
        super(AuthInitial()) {
    on<CheckAuthStatusEvent>((event, emit) async {
      emit(AuthLoading());
      try {
        final user = await _repository.getStoredUser();
        if (user != null) {
          emit(Authenticated(user));
        } else {
          emit(Unauthenticated());
        }
      } catch (_) {
        emit(Unauthenticated());
      }
    });

    on<LoginSubmittedEvent>((event, emit) async {
      emit(AuthLoading());
      try {
        final user = await _repository.login(
          email: event.email,
          password: event.password,
        );
        emit(Authenticated(user));
      } catch (e) {
        emit(AuthFailure(e.toString().replaceAll("Exception: ", "")));
      }
    });

    on<LogoutRequestedEvent>((event, emit) async {
      emit(AuthLoading());
      await _repository.logout();
      emit(Unauthenticated());
    });

    on<Toggle2FAEvent>((event, emit) async {
      if (state is Authenticated) {
        final current = (state as Authenticated).user;
        try {
          final isEnabled = await _repository.toggle2FA();
          final updated = UserModel(
            id: current.id,
            email: current.email,
            role: current.role,
            phone: current.phone,
            is2faEnabled: isEnabled,
            displayName: current.displayName,
          );
          emit(Authenticated(updated));
        } catch (_) {}
      }
    });
  }
}
