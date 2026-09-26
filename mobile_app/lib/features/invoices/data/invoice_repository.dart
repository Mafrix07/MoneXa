import 'package:monexa/core/network/api_client.dart';
import 'package:monexa/core/network/api_endpoints.dart';

class InvoiceItem {
  final int id;
  final String reference;
  final String monexaRef;
  final String clientName;
  final String clientPhone;
  final double amount;
  final String issueDate;
  final String dueDate;
  final String status;
  final String statusDisplay;

  InvoiceItem({
    required this.id,
    required this.reference,
    required this.monexaRef,
    required this.clientName,
    required this.clientPhone,
    required this.amount,
    required this.issueDate,
    required this.dueDate,
    required this.status,
    required this.statusDisplay,
  });

  factory InvoiceItem.fromJson(Map<String, dynamic> json) {
    return InvoiceItem(
      id: json['id'] ?? 0,
      reference: json['reference'] ?? '',
      monexaRef: json['monexa_ref'] ?? '',
      clientName: json['client_name'] ?? '',
      clientPhone: json['client_phone'] ?? '',
      amount: double.tryParse('${json['amount']}') ?? 0,
      issueDate: json['issue_date']?.toString() ?? '',
      dueDate: json['due_date']?.toString() ?? '',
      status: json['status'] ?? '',
      statusDisplay: json['status_display'] ?? json['status'] ?? '',
    );
  }
}

class InvoiceRepository {
  final ApiClient _client = ApiClient();

  Future<List<InvoiceItem>> list({String? query, String? status}) async {
    final params = <String, dynamic>{};
    if (query != null && query.isNotEmpty) params['search'] = query;
    if (status != null && status.isNotEmpty) params['status'] = status;
    final response = await _client.dio.get(ApiEndpoints.invoices, queryParameters: params);
    final data = response.data;
    final results = data is Map ? (data['results'] as List? ?? []) : (data as List? ?? []);
    return results.map((row) => InvoiceItem.fromJson(Map<String, dynamic>.from(row))).toList();
  }

  Future<InvoiceItem> create({
    required String clientName,
    String clientPhone = '',
    required String amount,
    required String issueDate,
    required String dueDate,
  }) async {
    final response = await _client.dio.post(ApiEndpoints.invoices, data: {
      'client_name': clientName,
      'client_phone': clientPhone,
      'amount': amount,
      'issue_date': issueDate,
      'due_date': dueDate,
    });
    return InvoiceItem.fromJson(Map<String, dynamic>.from(response.data));
  }
}
