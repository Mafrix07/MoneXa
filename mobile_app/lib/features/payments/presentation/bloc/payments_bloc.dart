import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/payment_repository.dart';

// Events
abstract class PaymentsEvent {}

class LoadPaymentsEvent extends PaymentsEvent {
  final String? status;
  LoadPaymentsEvent({this.status});
}

class ValidatePaymentActionSubmittedEvent extends PaymentsEvent {
  final int paymentId;
  final String action; // 'APPROVE' ou 'REJECT'
  final String? currentFilterStatus;
  ValidatePaymentActionSubmittedEvent({
    required this.paymentId,
    required this.action,
    this.currentFilterStatus,
  });
}

// States
abstract class PaymentsState {}

class PaymentsInitial extends PaymentsState {}

class PaymentsLoading extends PaymentsState {}

class PaymentsLoaded extends PaymentsState {
  final List<PaymentItem> payments;
  final String activeFilter;
  PaymentsLoaded({required this.payments, this.activeFilter = 'TOUS'});
}

class PaymentsError extends PaymentsState {
  final String message;
  PaymentsError(this.message);
}

// BLoC
class PaymentsBloc extends Bloc<PaymentsEvent, PaymentsState> {
  final PaymentRepository _repository;

  PaymentsBloc({PaymentRepository? repository})
      : _repository = repository ?? PaymentRepository(),
        super(PaymentsInitial()) {
    on<LoadPaymentsEvent>((event, emit) async {
      emit(PaymentsLoading());
      try {
        final list = await _repository.getPayments(status: event.status);
        emit(PaymentsLoaded(payments: list, activeFilter: event.status ?? 'TOUS'));
      } catch (e) {
        emit(PaymentsError(e.toString().replaceAll("Exception: ", "")));
      }
    });

    on<ValidatePaymentActionSubmittedEvent>((event, emit) async {
      try {
        await _repository.validatePayment(event.paymentId, action: event.action);
        // Recharger la liste après validation
        final list = await _repository.getPayments(status: event.currentFilterStatus);
        emit(
          PaymentsLoaded(
            payments: list,
            activeFilter: event.currentFilterStatus ?? 'TOUS',
          ),
        );
      } catch (e) {
        emit(PaymentsError(e.toString().replaceAll("Exception: ", "")));
      }
    });
  }
}
