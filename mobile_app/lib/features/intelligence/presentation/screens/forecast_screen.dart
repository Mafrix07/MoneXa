import 'package:flutter/material.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/intelligence/data/intelligence_repository.dart';
import 'package:monexa/shared/utils/formatters.dart';

class ForecastScreen extends StatefulWidget {
  const ForecastScreen({super.key});

  @override
  State<ForecastScreen> createState() => _ForecastScreenState();
}

class _ForecastScreenState extends State<ForecastScreen> {
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
      final data = await _repo.forecast();
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Prévisions réservées au comptable / gérant.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final expl = Map<String, dynamic>.from(_data['explanation'] as Map? ?? {});
    final points = Map<String, dynamic>.from(expl['points'] as Map? ?? {});
    final factors = List.from(expl['factors'] ?? []);
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Prévisions')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _point('Aujourd\'hui', points['today']),
                    _point('J+7', points['j7']),
                    _point('J+15', points['j15']),
                    _point('J+30', points['j30']),
                    const SizedBox(height: 16),
                    const Text('Pourquoi la trésorerie évolue-t-elle ainsi ?',
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                    const SizedBox(height: 8),
                    Text(
                      (expl['disclaimer'] ?? '').toString(),
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    if (factors.isEmpty)
                      const Text(
                        'Aucun facteur supplémentaire en base au-delà du modèle Holt-Winters.',
                        style: TextStyle(color: AppColors.textMuted),
                      ),
                    ...factors.map((raw) {
                      final f = Map<String, dynamic>.from(raw as Map);
                      final value = f['value'];
                      final shown = value is num ? Formatters.formatFcfa(value.toDouble()) : '$value';
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        title: Text(f['label']?.toString() ?? ''),
                        trailing: Text(shown, style: const TextStyle(fontWeight: FontWeight.w700)),
                      );
                    }),
                    const SizedBox(height: 8),
                    Text(
                      (_data['model'] ?? expl['model'] ?? '').toString(),
                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                    ),
                  ],
                ),
    );
  }

  Widget _point(String label, dynamic value) {
    final n = (value as num?)?.toDouble() ?? 0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(Formatters.formatFcfa(n), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        ],
      ),
    );
  }
}
