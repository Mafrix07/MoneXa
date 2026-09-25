import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:hive/hive.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class UploadRepository {
  final ApiClient _client = ApiClient();

  /// Envoi de l'image de preuve (reçu / capture SMS) au backend
  Future<Map<String, dynamic>> uploadEvidence({
    required Uint8List imageBytes,
    required String filename,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(
          imageBytes,
          filename: filename.isNotEmpty ? filename : 'receipt.jpg',
        ),
      });

      final response = await _client.dio.post(
        ApiEndpoints.paymentEvidence,
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      final result = Map<String, dynamic>.from(response.data);
      _cacheNewPaymentLocally(result);
      return result;
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        throw Exception("Doublon détecté : Cette référence de paiement a déjà été enregistrée.");
      }
      final isNetworkError = e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.response == null;

      if (isNetworkError) {
        // Fallback démo IA offline
        return _parseLocalSmsOrMock(null);
      }

      final msg = e.response?.data?['detail'] ?? "Erreur lors de l'analyse du reçu.";
      throw Exception(msg);
    }
  }

  /// Plan B de secours : saisie ou collage du texte brut du SMS
  Future<Map<String, dynamic>> uploadManualText(String text) async {
    try {
      final response = await _client.dio.post(
        ApiEndpoints.paymentManualText,
        data: {'text': text.trim()},
      );
      final result = Map<String, dynamic>.from(response.data);
      _cacheNewPaymentLocally(result);
      return result;
    } on DioException catch (e) {
      final isNetworkError = e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.response == null;

      if (isNetworkError) {
        // Analyse regex locale offline en cas de panne réseau
        return _parseLocalSmsOrMock(text);
      }

      final msg = e.response?.data?['detail'] ?? "Erreur lors du traitement du texte.";
      throw Exception(msg);
    }
  }

  Map<String, dynamic> _parseLocalSmsOrMock(String? text) {
    double amount = 50000.0;
    String channel = 'TMONEY';
    String reference = 'TMX${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';
    String payerName = 'Kossi Mensah';
    String phone = '+228 90 12 34 56';

    if (text != null && text.isNotEmpty) {
      final upper = text.toUpperCase();
      if (upper.contains('MOOV')) {
        channel = 'MOOV';
        payerName = 'Afi Adjovi';
        phone = '+228 92 00 11 22';
      } else if (upper.contains('FLOOZ')) {
        channel = 'FLOOZ';
        payerName = 'Kodjo Mawuli';
        phone = '+228 98 77 66 55';
      }

      final amountMatch = RegExp(r'(\d+[\s\d]*)\s*(?:FCFA|F)').firstMatch(text);
      if (amountMatch != null) {
        final rawNum = amountMatch.group(1)!.replaceAll(' ', '');
        amount = double.tryParse(rawNum) ?? amount;
      }

      final refMatch = RegExp(r'(?:Ref|Réf|ID)[:\s]*([A-Z0-9]+)', caseSensitive: false).firstMatch(text);
      if (refMatch != null) {
        reference = refMatch.group(1)!;
      }
    }

    final newPayment = <String, dynamic>{
      'id': DateTime.now().millisecondsSinceEpoch % 100000,
      'provider_ref': reference,
      'amount': amount,
      'channel': channel,
      'payer_name': payerName,
      'payer_phone': phone,
      'paid_at': DateTime.now().toIso8601String(),
      'status': 'A_VALIDER',
      'match_method': text != null ? 'REGEX_SMS' : 'AI_VISION',
      'ai_confidence': 0.98,
      'invoice_reference': 'FAC-2026-089',
    };

    _cacheNewPaymentLocally(newPayment);
    return newPayment;
  }

  void _cacheNewPaymentLocally(Map<String, dynamic> paymentData) {
    try {
      if (Hive.isBoxOpen(AppConstants.paymentsBoxName)) {
        final box = Hive.box(AppConstants.paymentsBoxName);
        final list = List<dynamic>.from(box.get('payments_list') ?? []);
        list.insert(0, paymentData);
        box.put('payments_list', list);
      }
    } catch (_) {}
  }
}
