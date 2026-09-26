import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/invoices/data/invoice_repository.dart';

class InvoiceCreateScreen extends StatefulWidget {
  const InvoiceCreateScreen({super.key});

  @override
  State<InvoiceCreateScreen> createState() => _InvoiceCreateScreenState();
}

class _InvoiceCreateScreenState extends State<InvoiceCreateScreen> {
  final _form = GlobalKey<FormState>();
  final _client = TextEditingController();
  final _phone = TextEditingController();
  final _amount = TextEditingController();
  DateTime _issue = DateTime.now();
  DateTime _due = DateTime.now().add(const Duration(days: 7));
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _client.dispose();
    _phone.dispose();
    _amount.dispose();
    super.dispose();
  }

  String _ymd(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Future<void> _pickDue() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _due,
      firstDate: _issue,
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _due = picked);
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final created = await InvoiceRepository().create(
        clientName: _client.text.trim(),
        clientPhone: _phone.text.trim(),
        amount: _amount.text.trim(),
        issueDate: _ymd(_issue),
        dueDate: _ymd(_due),
      );
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text(created.reference),
          content: Text('Référence de paiement à communiquer : ${created.monexaRef}'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
          ],
        ),
      );
      if (!mounted) return;
      context.pop(true);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = 'Création impossible. Vérifiez le montant et la connexion.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Nouvelle facture')),
      body: Form(
        key: _form,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _client,
              decoration: const InputDecoration(labelText: 'Client'),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Nom requis' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _phone,
              decoration: const InputDecoration(labelText: 'Téléphone'),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _amount,
              decoration: const InputDecoration(labelText: 'Montant (FCFA)'),
              keyboardType: TextInputType.number,
              validator: (v) {
                final n = double.tryParse((v ?? '').replaceAll(' ', ''));
                if (n == null || n <= 0) return 'Montant invalide';
                return null;
              },
            ),
            const SizedBox(height: 12),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Échéance'),
              subtitle: Text(_ymd(_due)),
              trailing: const Icon(Icons.event),
              onTap: _pickDue,
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(_error!, style: const TextStyle(color: AppColors.destructive)),
              ),
            ElevatedButton(
              onPressed: _saving ? null : _submit,
              child: _saving
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Créer la facture'),
            ),
          ],
        ),
      ),
    );
  }
}
