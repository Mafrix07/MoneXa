import 'package:flutter/material.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/intelligence/data/intelligence_repository.dart';
import 'package:monexa/shared/utils/formatters.dart';

class AnomaliesScreen extends StatefulWidget {
  const AnomaliesScreen({super.key});

  @override
  State<AnomaliesScreen> createState() => _AnomaliesScreenState();
}

class _AnomaliesScreenState extends State<AnomaliesScreen> {
  final _repo = IntelligenceRepository();
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _data = {};

  static const labels = {
    'doublon_potentiel': 'Doublon potentiel',
    'paiement_non_rattache': 'Paiement non rattaché',
    'montant_incoherent': 'Montant incohérent',
    'anomalie_comportementale': 'Anomalie comportementale',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _repo.anomalies();
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Accès réservé au gérant, ou erreur réseau.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final cats = _data['categories'] as Map? ?? {};
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Anomalies')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(_error!)))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(
                      (_data['disclaimer'] ?? 'Anomalie détectée — pas une qualification de fraude.')
                          .toString(),
                      style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    ...labels.entries.map((e) {
                      final items = List.from(cats[e.key] ?? []);
                      return _section(e.value, items);
                    }),
                  ],
                ),
    );
  }

  Widget _section(String title, List items) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          const SizedBox(height: 8),
          if (items.isEmpty)
            const Text('Aucune', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ...items.map((raw) {
            final m = Map<String, dynamic>.from(raw as Map);
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: Text(
                '${m['label'] ?? 'Anomalie détectée'}\n'
                '${m['provider_ref'] ?? ''}  ${m['amount'] != null ? Formatters.formatFcfa((m['amount'] as num).toDouble()) : ''}\n'
                '${m['type'] ?? ''} — ${m['description'] ?? ''}',
                style: const TextStyle(fontSize: 13, height: 1.35),
              ),
            );
          }),
        ],
      ),
    );
  }
}
