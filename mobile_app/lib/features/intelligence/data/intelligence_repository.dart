import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class IntelligenceRepository {
  final ApiClient _client = ApiClient();

  Future<List<dynamic>> listSources() async {
    final r = await _client.dio.get(ApiEndpoints.sources);
    final data = r.data;
    if (data is List) return data;
    return data['results'] ?? [];
  }

  Future<Map<String, dynamic>> syncSource(int id) async {
    final r = await _client.dio.post(ApiEndpoints.syncSource(id));
    return Map<String, dynamic>.from(r.data);
  }

  Future<Map<String, dynamic>> anomalies() async {
    final r = await _client.dio.get(ApiEndpoints.anomalies);
    return Map<String, dynamic>.from(r.data);
  }

  Future<Map<String, dynamic>> forecast() async {
    final r = await _client.dio.get(
      ApiEndpoints.forecast,
      queryParameters: {'days': 30},
    );
    return Map<String, dynamic>.from(r.data);
  }

  Future<Map<String, dynamic>> explainPayment(int id) async {
    final r = await _client.dio.get(ApiEndpoints.explainPayment(id));
    return Map<String, dynamic>.from(r.data);
  }

  Future<List<dynamic>> auditLogs() async {
    final r = await _client.dio.get(ApiEndpoints.auditLogs);
    final data = r.data;
    if (data is List) return data;
    return data['results'] ?? [];
  }
}
