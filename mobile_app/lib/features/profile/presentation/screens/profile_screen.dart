import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:hive/hive.dart';
import 'package:monexa/core/constants/app_constants.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/features/auth/presentation/bloc/auth_bloc.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _selectedLanguage = AppConstants.langFr;

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthBloc>().state;
    String email = 'utilisateur@monexa.tg';
    String role = 'CAISSIER';
    String displayName = 'MoneXa User';
    bool is2faEnabled = false;

    if (authState is Authenticated) {
      email = authState.user.email;
      role = authState.user.role;
      displayName = authState.user.displayName;
      is2faEnabled = authState.user.is2faEnabled;
    }

    final isGerant = role == 'GERANT';

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Profil & Paramètres'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Carte Utilisateur
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                    child: Text(
                      displayName.isNotEmpty ? displayName[0].toUpperCase() : 'U',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          displayName,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          email,
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            role,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Section Sécurité
            const Text(
              'Sécurité & Authentification',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 10),
            Container(
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: SwitchListTile(
                title: const Text('Authentification à 2 facteurs (2FA TOTP)', style: TextStyle(fontSize: 14)),
                subtitle: Text(
                  isGerant
                      ? (is2faEnabled ? 'Activé (Google Authenticator / Authy)' : 'Optionnel pour le Gérant')
                      : 'Réservé au rôle Gérant',
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                value: is2faEnabled,
                activeThumbColor: AppColors.accent,
                onChanged: isGerant
                    ? (val) {
                        context.read<AuthBloc>().add(Toggle2FAEvent());
                      }
                    : null,
              ),
            ),

            const SizedBox(height: 20),

            // Section Inclusion Linguistique (Cahier des charges §14.1)
            const Text(
              'Inclusion Linguistique (Langues Locales)',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Langue de l\'interface :',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    children: [
                      ChoiceChip(
                        label: const Text('🇫🇷 Français'),
                        selected: _selectedLanguage == AppConstants.langFr,
                        onSelected: (val) {
                          if (val) setState(() => _selectedLanguage = AppConstants.langFr);
                        },
                      ),
                      ChoiceChip(
                        label: const Text('🇹🇬 Ewé (Eʋegbe)'),
                        selected: _selectedLanguage == AppConstants.langEe,
                        onSelected: (val) {
                          if (val) setState(() => _selectedLanguage = AppConstants.langEe);
                        },
                      ),
                      ChoiceChip(
                        label: const Text('🇹🇬 Kabyé'),
                        selected: _selectedLanguage == AppConstants.langKab,
                        onSelected: (val) {
                          if (val) setState(() => _selectedLanguage = AppConstants.langKab);
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _selectedLanguage == AppConstants.langFr
                        ? 'Interface en Français standard.'
                        : 'Traduction active des libellés et aides vocales.',
                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Cache & Offline-first info
            const Text(
              'Stockage Hors-Ligne (Hive)',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Cache local actif', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      Text('Paiements & KPIs synchronisés', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                    ],
                  ),
                  OutlinedButton(
                    onPressed: () async {
                      final messenger = ScaffoldMessenger.of(context);
                      if (Hive.isBoxOpen(AppConstants.kpiBoxName)) {
                        await Hive.box(AppConstants.kpiBoxName).clear();
                      }
                      if (Hive.isBoxOpen(AppConstants.paymentsBoxName)) {
                        await Hive.box(AppConstants.paymentsBoxName).clear();
                      }
                      if (mounted) {
                        messenger.showSnackBar(
                          const SnackBar(content: Text('Cache local vidé.')),
                        );
                      }
                    },
                    child: const Text('Vider le cache', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // Déconnexion
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.destructive,
                foregroundColor: Colors.white,
              ),
              icon: const Icon(Icons.logout_rounded, size: 18),
              label: const Text('Se déconnecter'),
              onPressed: () {
                context.read<AuthBloc>().add(LogoutRequestedEvent());
                context.go('/login');
              },
            ),

            const SizedBox(height: 20),
            const Center(
              child: Text(
                'MoneXa v1.0.0 — ESIG Tech Arena 2026 (Défi 2)',
                style: TextStyle(fontSize: 11, color: AppColors.textMuted),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
