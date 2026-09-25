import 'package:flutter_test/flutter_test.dart';
import 'package:monexa/features/payments/data/payment_repository.dart';
import 'package:monexa/features/payments/presentation/bloc/payments_bloc.dart';

class FakePaymentRepository extends PaymentRepository {
  List<PaymentItem> mockPayments = [];
  bool shouldFail = false;

  @override
  Future<List<PaymentItem>> getPayments({String? status}) async {
    if (shouldFail) {
      throw Exception('Erreur réseau paiements');
    }
    if (status == null || status == 'TOUS') {
      return mockPayments;
    }
    return mockPayments.where((p) => p.status == status).toList();
  }

  @override
  Future<void> validatePayment(int paymentId, {required String action}) async {
    final idx = mockPayments.indexWhere((p) => p.id == paymentId);
    if (idx != -1) {
      final old = mockPayments[idx];
      mockPayments[idx] = PaymentItem(
        id: old.id,
        providerRef: old.providerRef,
        amount: old.amount,
        channel: old.channel,
        payerName: old.payerName,
        payerPhone: old.payerPhone,
        paidAt: old.paidAt,
        status: action == 'APPROVE' ? 'RECONCILIE' : 'NON_RATTACHE',
        matchMethod: old.matchMethod,
        aiConfidence: old.aiConfidence,
        invoiceRef: old.invoiceRef,
      );
    }
  }
}

void main() {
  group('PaymentsBloc tests', () {
    late FakePaymentRepository fakeRepo;
    late PaymentsBloc paymentsBloc;

    final samplePayment = PaymentItem(
      id: 101,
      providerRef: 'TMX98234710',
      amount: 50000.0,
      channel: 'TMONEY',
      payerName: 'Kossi Mensah',
      payerPhone: '+228 90 12 34 56',
      paidAt: '2026-09-25T14:30:00Z',
      status: 'A_VALIDER',
      matchMethod: 'AI_VISION',
      aiConfidence: 0.98,
      invoiceRef: 'FAC-2026-089',
    );

    setUp(() {
      fakeRepo = FakePaymentRepository();
      fakeRepo.mockPayments = [samplePayment];
      paymentsBloc = PaymentsBloc(repository: fakeRepo);
    });

    tearDown(() {
      paymentsBloc.close();
    });

    test('Initial state is PaymentsInitial', () {
      expect(paymentsBloc.state, isA<PaymentsInitial>());
    });

    test('LoadPaymentsEvent emits PaymentsLoading then PaymentsLoaded', () async {
      paymentsBloc.add(LoadPaymentsEvent(status: 'TOUS'));

      await expectLater(
        paymentsBloc.stream,
        emitsInOrder([
          isA<PaymentsLoading>(),
          predicate<PaymentsState>((state) {
            return state is PaymentsLoaded &&
                state.payments.length == 1 &&
                state.payments.first.providerRef == 'TMX98234710';
          }),
        ]),
      );
    });

    test('ValidatePaymentActionSubmittedEvent approves and reloads payment list', () async {
      paymentsBloc.add(
        ValidatePaymentActionSubmittedEvent(
          paymentId: 101,
          action: 'APPROVE',
          currentFilterStatus: 'TOUS',
        ),
      );

      await expectLater(
        paymentsBloc.stream,
        emitsInOrder([
          predicate<PaymentsState>((state) {
            return state is PaymentsLoaded &&
                state.payments.first.status == 'RECONCILIE';
          }),
        ]),
      );
    });
  });
}
