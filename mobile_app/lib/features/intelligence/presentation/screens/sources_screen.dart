import 'package:flutter/material.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/intelligence/data/intelligence_repository.dart';

class SourcesScreen extends StatefulWidget {
  const SourcesScreen({super.key});

  @override
  State<SourcesScreen> createState() => _SourcesScreenState();
}

class _SourcesScreenState extends State<SourcesScreen> {
  final _repo = IntelligenceRepository();
  bool _loading = true;
  String? _error;
  List<dynamic> _sources = [];

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
      final list = await _repo.listSources();
      setState(() {
        _sources = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _loading = false;
      });
    }
  }

  Future<void> _sync(int id) async {
    try {
      await _repo.syncSource(id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Synchronisation simulée terminée (aucune API opérateur réelle).'),
        ),
      );
      _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppColors.destructive),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Sources financières')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    const Text(
                      'Les connecteurs T-Money, Moov, Flooz et banque sont simulés. '
                      'Aucune API opérateur n’est appelée.',
                      style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    ..._sources.map((raw) {
                      final s = Map<String, dynamic>.from(raw as Map);
                      final simulated = s['is_simulated'] == true;
                      final status = (s['status'] ?? '').toString();
                      final color = status == 'ERROR'
                          ? AppColors.destructive
                          : status == 'ACTIVE'
                              ? AppColors.success
                              : AppColors.accent;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppColors.borderLight),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.circle, size: 10, color: color),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    s['name']?.toString() ?? '',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w800,
                                      fontSize: 16,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text(
                              [
                                s['integration_method_display'],
                                if ((s['merchant_mask'] ?? '').toString().isNotEmpty)
                                  s['merchant_mask'],
                                simulated ? 'Connecteur simulé' : 'Live',
                              ].where((e) => e != null && e.toString().isNotEmpty).join(' • '),
                              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Dernière sync : ${s['last_sync_at'] ?? '—'}  ·  ${s['transaction_count'] ?? 0} écritures',
                              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                            ),
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton(
                                onPressed: () => _sync(s['id'] as int),
                                child: const Text('Synchroniser'),
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
    );
  }
}
