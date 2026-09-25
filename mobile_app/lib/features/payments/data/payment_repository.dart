import 'package:hive/hive.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class PaymentItem {
  final int id;
  final String providerRef;
  final double amount;
  final String channel;
  final String payerName;
  final String payerPhone;
  final String paidAt;
  final String status;
  final String matchMethod;
  final double aiConfidence;
  final String? invoiceRef;

  PaymentItem({
    required this.id,
    required this.providerRef,
    required this.amount,
    required this.channel,
    required this.payerName,
    required this.payerPhone,
    required this.paidAt,
    required this.status,
    required this.matchMethod,
    required this.aiConfidence,
    this.invoiceRef,
  });

  factory PaymentItem.fromJson(Map<String, dynamic> json) {
    return PaymentItem(
      id: json['id'] ?? 0,
      providerRef: json['provider_ref'] ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      channel: json['channel'] ?? 'TMONEY',
      payerName: json['payer_name'] ?? 'Inconnu',
      payerPhone: json['payer_phone'] ?? '',
      paidAt: json['paid_at'] ?? '',
      status: json['status'] ?? 'NON_RATTACHE',
      matchMethod: json['match_method'] ?? 'MANUEL',
      aiConfidence: (json['ai_confidence'] as num?)?.toDouble() ?? 0.0,
      invoiceRef: json['invoice_reference'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'provider_ref': providerRef,
      'amount': amount,
      'channel': channel,
      'payer_name': payerName,
      'payer_phone': payerPhone,
      'paid_at': paidAt,
      'status': status,
      'match_method': matchMethod,
      'ai_confidence': aiConfidence,
      'invoice_reference': invoiceRef,
    };
  }
}

class PaymentRepository {
  final ApiClient _client = ApiClient();

  Future<List<PaymentItem>> getPayments({String? status}) async {
    final box = Hive.isBoxOpen(AppConstants.paymentsBoxName)
        ? Hive.box(AppConstants.paymentsBoxName)
        : await Hive.openBox(AppConstants.paymentsBoxName);

    try {
      final queryParams = <String, dynamic>{};
      if (status != null && status.isNotEmpty && status != 'TOUS') {
        queryParams['status'] = status;
      }

      final response = await _client.dio.get(
        ApiEndpoints.payments,
        queryParameters: queryParams,
      );

      final List rawList = response.data is List
          ? response.data
          : (response.data['results'] ?? []);

      final list = rawList
          .map((item) => PaymentItem.fromJson(Map<String, dynamic>.from(item)))
          .toList();

      // Cacher les données dans Hive
      if (status == null || status == 'TOUS') {
        await box.put('payments_list', rawList);
      }

      return list;
    } catch (_) {
      // Offline-First : charger depuis Hive si disponible
      final cached = box.get('payments_list') as List?;
      if (cached != null) {
        var items = cached
            .map((item) => PaymentItem.fromJson(Map<String, dynamic>.from(item)))
            .toList();
        if (status != null && status.isNotEmpty && status != 'TOUS') {
          items = items.where((p) => p.status == status).toList();
        }
        return items;
      }

      // Données démo offline par défaut
      final defaultList = <Map<String, dynamic>>[
        {
          'id': 101,
          'provider_ref': 'TMX98234710',
          'amount': 50000.0,
          'channel': 'TMONEY',
          'payer_name': 'Kossi Mensah',
          'payer_phone': '+228 90 12 34 56',
          'paid_at': '2026-09-25T14:30:00Z',
          'status': 'A_VALIDER',
          'match_method': 'AI_VISION',
          'ai_confidence': 0.98,
          'invoice_reference': 'FAC-2026-089',
        },
        {
          'id': 102,
          'provider_ref': 'MV8820311',
          'amount': 120000.0,
          'channel': 'MOOV',
          'payer_name': 'Afi Adjovi',
          'payer_phone': '+228 92 00 11 22',
          'paid_at': '2026-09-25T11:15:00Z',
          'status': 'RECONCILIE',
          'match_method': 'AUTOMATIQUE',
          'ai_confidence': 0.99,
          'invoice_reference': 'FAC-2026-074',
        },
        {
          'id': 103,
          'provider_ref': 'FLZ449102',
          'amount': 75000.0,
          'channel': 'FLOOZ',
          'payer_name': 'Entreprise Kodjo & Fils',
          'payer_phone': '+228 99 44 55 66',
          'paid_at': '2026-09-24T16:45:00Z',
          'status': 'ANOMALIE',
          'match_method': 'MANUEL',
          'ai_confidence': 0.65,
          'invoice_reference': null,
        },
        {
          'id': 104,
          'provider_ref': 'TMX9811200',
          'amount': 35000.0,
          'channel': 'TMONEY',
          'payer_name': 'Supermarché Champion Lomé',
          'payer_phone': '+228 91 33 22 11',
          'paid_at': '2026-09-24T09:10:00Z',
          'status': 'RECONCILIE',
          'match_method': 'AUTOMATIQUE',
          'ai_confidence': 1.0,
          'invoice_reference': 'FAC-2026-068',
        },
      ];
      await box.put('payments_list', defaultList);

      var items = defaultList
          .map((item) => PaymentItem.fromJson(item))
          .toList();
      if (status != null && status.isNotEmpty && status != 'TOUS') {
        items = items.where((p) => p.status == status).toList();
      }
      return items;
    }
  }

  Future<void> validatePayment(int paymentId, {required String action}) async {
    final box = Hive.isBoxOpen(AppConstants.paymentsBoxName)
        ? Hive.box(AppConstants.paymentsBoxName)
        : await Hive.openBox(AppConstants.paymentsBoxName);

    try {
      await _client.dio.patch(
        ApiEndpoints.validatePayment(paymentId),
        data: {'action': action},
      );
    } catch (_) {
      // Fallback offline : on met à jour localement dans Hive
    }

    final cached = box.get('payments_list') as List?;
    if (cached != null) {
      final updated = cached.map((raw) {
        final map = Map<String, dynamic>.from(raw);
        if (map['id'] == paymentId) {
          map['status'] = action == 'APPROVE' ? 'RECONCILIE' : 'NON_RATTACHE';
        }
        return map;
      }).toList();
      await box.put('payments_list', updated);
    }
  }
}
