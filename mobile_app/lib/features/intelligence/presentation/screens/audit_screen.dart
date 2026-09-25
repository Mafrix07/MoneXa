import 'package:flutter/material.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/intelligence/data/intelligence_repository.dart';

class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});

  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  final _repo = IntelligenceRepository();
  bool _loading = true;
  String? _error;
  List<dynamic> _logs = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final logs = await _repo.auditLogs();
      setState(() {
        _logs = logs;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Journal réservé au gérant.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Journal d\'audit')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    const Text(
                      'Immuabilité : couche Python (save/delete bloqués) + chaîne SHA-256. '
                      'Aucun trigger PostgreSQL n\'est installé dans ce prototype.',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    ..._logs.map((raw) {
                      final l = Map<String, dynamic>.from(raw as Map);
                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.borderLight),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${l['timestamp'] ?? ''}  ·  ${l['user_email'] ?? ''} (${l['user_role'] ?? ''})',
                              style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${l['action']}  ${l['entity']}:${l['entity_id']}',
                              style: const TextStyle(fontWeight: FontWeight.w700),
                            ),
                            Text(
                              'hash ${l['hash_short'] ?? ''}',
                              style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
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
