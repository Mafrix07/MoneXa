import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/invoices/data/invoice_repository.dart';
import 'package:monexa/shared/utils/formatters.dart';
import 'package:monexa/shared/widgets/status_badge.dart';

class InvoicesScreen extends StatefulWidget {
  const InvoicesScreen({super.key});

  @override
  State<InvoicesScreen> createState() => _InvoicesScreenState();
}

class _InvoicesScreenState extends State<InvoicesScreen> {
  final _repo = InvoiceRepository();
  final _search = TextEditingController();
  List<InvoiceItem> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final rows = await _repo.list(query: _search.text.trim());
      if (!mounted) return;
      setState(() {
        _items = rows;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Impossible de charger les factures.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Factures'),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await context.push<bool>('/invoices/new');
          if (created == true) _load();
        },
        backgroundColor: AppColors.accent,
        foregroundColor: const Color(0xFF1A1408),
        icon: const Icon(Icons.add),
        label: const Text('Créer'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _search,
              decoration: InputDecoration(
                hintText: 'Charger : réf, MXA, client',
                suffixIcon: IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: _load,
                ),
              ),
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _load(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
                : _error != null
                    ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.textSecondary)))
                    : _items.isEmpty
                        ? const Center(child: Text('Aucune facture. Créez-en une.'))
                        : RefreshIndicator(
                            onRefresh: _load,
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 0, 16, 88),
                              itemCount: _items.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 8),
                              itemBuilder: (context, i) {
                                final inv = _items[i];
                                return Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: AppColors.surface,
                                    borderRadius: BorderRadius.circular(14),
                                    border: Border.all(color: AppColors.borderLight),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              inv.reference,
                                              style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.textPrimary),
                                            ),
                                          ),
                                          StatusBadge(status: inv.status),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      Text(inv.clientName, style: const TextStyle(fontWeight: FontWeight.w600)),
                                      Text(
                                        '${inv.monexaRef} · ${Formatters.formatFcfa(inv.amount)}',
                                        style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                                      ),
                                      Text(
                                        'Échéance ${Formatters.formatShortDate(inv.dueDate)}',
                                        style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
