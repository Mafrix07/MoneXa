import 'package:flutter/material.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/intelligence/data/intelligence_repository.dart';
import 'package:monexa/shared/utils/formatters.dart';

class ExplainScreen extends StatefulWidget {
  final int paymentId;
  const ExplainScreen({super.key, required this.paymentId});

  @override
  State<ExplainScreen> createState() => _ExplainScreenState();
}

class _ExplainScreenState extends State<ExplainScreen> {
  final _repo = IntelligenceRepository();
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _data = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _repo.explainPayment(widget.paymentId);
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final invoice = _data['invoice'] as Map?;
    final criteria = List.from(_data['criteria'] ?? []);
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Réconciliation')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(
                      _data['decision_label']?.toString() ?? '',
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${Formatters.formatFcfa(double.tryParse('${_data['amount']}') ?? 0)}  ·  ${_data['payer_name'] ?? ''}  ·  ${_data['provider_ref'] ?? ''}',
                    ),
                    if (invoice != null) ...[
                      const SizedBox(height: 12),
                      Text(
                        'Facture ${invoice['reference']}  ${invoice['client_name']}  ${invoice['amount']} FCFA',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ],
                    const SizedBox(height: 16),
                    const Text('Critères (moteur réel)', style: TextStyle(fontWeight: FontWeight.w800)),
                    ...criteria.map((raw) {
                      final c = Map<String, dynamic>.from(raw as Map);
                      final ok = c['matched'] == true;
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          ok ? Icons.check_circle : Icons.cancel_outlined,
                          color: ok ? AppColors.success : AppColors.textMuted,
                        ),
                        title: Text(c['label']?.toString() ?? ''),
                        subtitle: Text(c['value']?.toString() ?? ''),
                      );
                    }),
                    Text(
                      'Confiance : ${((_data['confidence'] as num?)?.toDouble() ?? 0) * 100 ~/ 1} %  (${_data['confidence_level'] ?? ''})',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      (_data['disclaimer'] ?? '').toString(),
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
    );
  }
}
