import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/shared/utils/formatters.dart';
import 'package:monexa/shared/widgets/status_badge.dart';
import 'package:monexa/features/upload_evidence/presentation/bloc/upload_bloc.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _smsTextController = TextEditingController();
  Uint8List? _selectedImageBytes;
  String _selectedImageName = '';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _smsTextController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 1200,
        maxHeight: 1200,
        imageQuality: 85,
      );

      if (file != null) {
        final bytes = await file.readAsBytes();
        setState(() {
          _selectedImageBytes = bytes;
          _selectedImageName = file.name;
        });

        if (mounted) {
          context.read<UploadBloc>().add(
                UploadImageSubmittedEvent(
                  imageBytes: bytes,
                  filename: file.name,
                ),
              );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Erreur sélection image: $e"),
            backgroundColor: AppColors.destructive,
          ),
        );
      }
    }
  }

  void _fillSampleSms(String text) {
    setState(() {
      _smsTextController.text = text;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Capture de Reçu'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.accent,
          indicatorWeight: 3,
          tabs: const [
            Tab(icon: Icon(Icons.camera_alt_outlined), text: 'Photo / Reçu'),
            Tab(icon: Icon(Icons.sms_outlined), text: 'SMS brut (Plan B)'),
          ],
        ),
      ),
      body: BlocConsumer<UploadBloc, UploadState>(
        listener: (context, state) {
          if (state is UploadFailure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.destructive,
                behavior: SnackBarBehavior.floating,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is UploadProcessing) {
            return _buildProcessingView(state);
          }

          if (state is UploadSuccess) {
            return _buildSuccessView(state.result);
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildCameraUploadTab(),
              _buildManualSmsTab(),
            ],
          );
        },
      ),
    );
  }

  // Onglet 1 : Upload Photo / Reçu
  Widget _buildCameraUploadTab() {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(28),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: AppColors.borderLight),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.02),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.08),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.document_scanner_rounded,
                    size: 56,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Photographiez un reçu ou un SMS',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'L\'IA multimodale extrait le montant, la référence et réconcilie la transaction avec vos factures.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            icon: const Icon(Icons.camera_alt),
            label: const Text('Prendre une photo'),
            onPressed: () => _pickImage(ImageSource.camera),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            icon: const Icon(Icons.photo_library_outlined),
            label: const Text('Choisir dans la galerie'),
            onPressed: () => _pickImage(ImageSource.gallery),
          ),
        ],
      ),
    );
  }

  // Onglet 2 : Plan B - Saisie texte SMS
  Widget _buildManualSmsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Plan B : Collez le texte du SMS reçu',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'En cas de mauvaise qualité d\'image ou indisponibilité réseau.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),

          // Chips démo
          const Text(
            'Exemples de SMS (démo rapide) :',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              ActionChip(
                label: const Text('T-Money 50 000 F'),
                onPressed: () => _fillSampleSms(
                  "Paiement recu de Kossi Mensah (90123456) de 50000 FCFA. Ref: TMX98234710 le 25/09/2026. Solde: 450000 FCFA.",
                ),
              ),
              ActionChip(
                label: const Text('Moov 120 000 F'),
                onPressed: () => _fillSampleSms(
                  "Vous avez recu 120000 FCFA de Afi Adjovi (+228 92001122). Ref: MV8820311 le 25/09/2026. Nouveau solde: 320000 FCFA.",
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _smsTextController,
            maxLines: 5,
            decoration: const InputDecoration(
              hintText: 'Collez ici le SMS reçu de l\'opérateur...',
            ),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            icon: const Icon(Icons.bolt),
            label: const Text('Analyser le SMS texte'),
            onPressed: () {
              if (_smsTextController.text.trim().isNotEmpty) {
                context.read<UploadBloc>().add(
                      UploadManualTextSubmittedEvent(_smsTextController.text.trim()),
                    );
              }
            },
          ),
        ],
      ),
    );
  }

  // Vue Chargement animé étapes IA
  Widget _buildProcessingView(UploadProcessing state) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_selectedImageBytes != null) ...[
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.primary, width: 2),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.2),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: Image.memory(
                    _selectedImageBytes!,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 90,
                  height: 90,
                  child: CircularProgressIndicator(
                    strokeWidth: 4,
                    valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                    backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                  ),
                ),
                const Icon(
                  Icons.psychology_outlined,
                  size: 40,
                  color: AppColors.primary,
                ),
              ],
            ),
            const SizedBox(height: 28),
            Text(
              state.stepMessage,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Analyse IA multimodale & contrôle financier en cours...',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Vue Résultat Extraction IA avec confirmation
  Widget _buildSuccessView(Map<String, dynamic> result) {
    final amount = result['amount'] ?? result['montant'] ?? 0;
    final operator = result['channel'] ?? result['operator'] ?? 'TMONEY';
    final ref = result['provider_ref'] ?? result['reference'] ?? '—';
    final payer = result['payer_name'] ?? result['emetteur'] ?? 'Payeur';
    final phone = result['payer_phone'] ?? result['telephone_emetteur'] ?? '';
    final status = result['status'] ?? 'A_VALIDER';
    final confidence = (result['ai_confidence'] as num?)?.toDouble() ?? 0.95;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.success.withValues(alpha: 0.4)),
              boxShadow: [
                BoxShadow(
                  color: AppColors.success.withValues(alpha: 0.08),
                  blurRadius: 15,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                if (_selectedImageBytes != null) ...[
                  Container(
                    height: 100,
                    width: 100,
                    margin: const EdgeInsets.only(bottom: 12),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.borderLight),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(_selectedImageBytes!, fit: BoxFit.cover),
                    ),
                  ),
                ],
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: const BoxDecoration(
                    color: Color(0xFFDCFCE7),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 40),
                ),
                const SizedBox(height: 14),
                const Text(
                  'Paiement Enregistré & Réconcilié !',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  Formatters.formatFcfa(amount),
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    StatusBadge(status: operator.toString(), isChannel: true),
                    const SizedBox(width: 8),
                    StatusBadge(status: status.toString()),
                  ],
                ),
                const Divider(height: 32),
                if (_selectedImageName.isNotEmpty)
                  _buildResultRow('Fichier analysé', _selectedImageName),
                _buildResultRow('Référence Opérateur', ref.toString()),
                _buildResultRow('Payeur', payer.toString()),
                if (phone.toString().isNotEmpty)
                  _buildResultRow('Téléphone', phone.toString()),
                _buildResultRow(
                  'Confiance IA',
                  '${(confidence * 100).toInt()}%',
                  valueColor: AppColors.success,
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => context.go('/payments'),
            child: const Text('Voir dans les paiements'),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: () {
              setState(() {
                _selectedImageBytes = null;
                _selectedImageName = '';
              });
              context.read<UploadBloc>().add(ResetUploadEvent());
            },
            child: const Text('Scanner un autre reçu'),
          ),
        ],
      ),
    );
  }

  Widget _buildResultRow(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: valueColor ?? AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}
