import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/shared/utils/formatters.dart';
import 'package:monexa/shared/widgets/kpi_card.dart';
import 'package:monexa/shared/widgets/monexa_logo.dart';
import 'package:monexa/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:monexa/features/dashboard/presentation/bloc/dashboard_bloc.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    context.read<DashboardBloc>().add(LoadDashboardEvent());
  }

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthBloc>().state;
    String userRole = 'Utilisateur';
    String userName = 'MoneXa User';
    if (authState is Authenticated) {
      userRole = authState.user.role;
      userName = authState.user.displayName;
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        leadingWidth: 132,
        leading: const Padding(
          padding: EdgeInsets.only(left: 12),
          child: Align(
            alignment: Alignment.centerLeft,
            child: MonexaLogo(height: 28, alignment: Alignment.centerLeft),
          ),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bonjour, $userName',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
            ),
            Text(
              'Rôle : $userRole',
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.smart_toy_outlined, color: AppColors.primary),
            tooltip: 'TresorIA Chatbot',
            onPressed: () => context.push('/assistant'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textPrimary),
            tooltip: 'Actualiser',
            onPressed: () => context.read<DashboardBloc>().add(RefreshDashboardEvent()),
          ),
        ],
      ),
      body: BlocBuilder<DashboardBloc, DashboardState>(
        builder: (context, state) {
          if (state is DashboardLoading) {
            return const _DashboardSkeleton();
          }

          if (state is DashboardError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.cloud_off_rounded, size: 54, color: AppColors.textMuted),
                    const SizedBox(height: 16),
                    Text(
                      'Erreur de chargement',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      state.message,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.refresh),
                      label: const Text('Réessayer'),
                      onPressed: () => context.read<DashboardBloc>().add(LoadDashboardEvent()),
                    ),
                  ],
                ),
              ),
            );
          }

          if (state is! DashboardLoaded) {
            return const SizedBox.shrink();
          }

          final data = state.data;

          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async {
              context.read<DashboardBloc>().add(RefreshDashboardEvent());
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Bandeau Offline-First si servi depuis Hive
                  if (data.isFromCache)
                    Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.accent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.accent.withValues(alpha: 0.4)),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.wifi_off_rounded, size: 16, color: AppColors.warning),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Mode hors-ligne : Données locales Hive affichées.',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // Carte Trésorerie Consolidée
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.primaryDark, AppColors.primary],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.primaryDark.withValues(alpha: 0.12),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Trésorerie consolidée',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          Formatters.formatFcfa(data.soldeTotal),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 26,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -0.5,
                          ),
                        ),
                        const SizedBox(height: 14),
                        Row(
                          children: [
                            const Icon(Icons.trending_up, color: AppColors.accent, size: 16),
                            const SizedBox(width: 4),
                            Text(
                              'Flux net 30j : ${Formatters.formatFcfa(data.fluxNet30j)}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),
                  if (data.charts.hasFlow)
                    Container(
                      padding: const EdgeInsets.fromLTRB(14, 14, 14, 8),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceVariant,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Flux 14 jours',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Paiements et dépenses du ledger',
                            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                          const SizedBox(height: 12),
                          SizedBox(
                            height: 120,
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                for (final day in data.charts.days)
                                  Expanded(
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 1),
                                      child: Column(
                                        children: [
                                          Expanded(
                                            child: Row(
                                              crossAxisAlignment: CrossAxisAlignment.end,
                                              children: [
                                                Expanded(
                                                  child: FractionallySizedBox(
                                                    heightFactor: (((day['encaisse_pct'] as num?)?.toDouble() ?? 0) / 100).clamp(0.0, 1.0),
                                                    alignment: Alignment.bottomCenter,
                                                    child: Container(
                                                      decoration: const BoxDecoration(
                                                        color: AppColors.primary,
                                                        borderRadius: BorderRadius.vertical(top: Radius.circular(2)),
                                                      ),
                                                    ),
                                                  ),
                                                ),
                                                const SizedBox(width: 1),
                                                Expanded(
                                                  child: FractionallySizedBox(
                                                    heightFactor: (((day['decaisse_pct'] as num?)?.toDouble() ?? 0) / 100).clamp(0.0, 1.0),
                                                    alignment: Alignment.bottomCenter,
                                                    child: Container(
                                                      decoration: const BoxDecoration(
                                                        color: AppColors.accent,
                                                        borderRadius: BorderRadius.vertical(top: Radius.circular(2)),
                                                      ),
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            '${day['label'] ?? ''}',
                                            style: const TextStyle(fontSize: 8, color: AppColors.textSecondary),
                                            overflow: TextOverflow.clip,
                                            maxLines: 1,
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  if (data.charts.hasFlow) const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ActionChip(
                        label: const Text('À valider'),
                        onPressed: () => context.go('/payments'),
                      ),
                      ActionChip(
                        label: const Text('Anomalies'),
                        onPressed: () => context.push('/anomalies'),
                      ),
                      ActionChip(
                        label: const Text('Prévisions'),
                        onPressed: () => context.push('/forecast'),
                      ),
                      ActionChip(
                        label: const Text('Sources'),
                        onPressed: () => context.push('/sources'),
                      ),
                      ActionChip(
                        label: const Text('Audit'),
                        onPressed: () => context.push('/audit'),
                      ),
                      ActionChip(
                        label: const Text('TresorIA'),
                        onPressed: () => context.go('/assistant'),
                      ),
                    ],
                  ),

                  const SizedBox(height: 18),

                  // Grille 4 KPI Cards
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.25,
                    children: [
                      KpiCard(
                        label: 'Encaissé 7j',
                        value: Formatters.formatFcfa(data.encaisse7j),
                        icon: Icons.arrow_downward_rounded,
                        color: AppColors.success,
                      ),
                      KpiCard(
                        label: 'Décaissé 7j',
                        value: Formatters.formatFcfa(data.decaisse7j),
                        icon: Icons.arrow_upward_rounded,
                        color: AppColors.warning,
                      ),
                      KpiCard(
                        label: 'À valider',
                        value: '${data.paiementsAValider} paiements',
                        icon: Icons.pending_actions_rounded,
                        color: AppColors.accent,
                        subtitle: 'Action requise',
                      ),
                      KpiCard(
                        label: 'Anomalies',
                        value: '${data.anomaliesNonResolues} alertes',
                        icon: Icons.warning_amber_rounded,
                        color: AppColors.destructive,
                        subtitle: data.anomaliesNonResolues > 0 ? 'À vérifier' : 'Sain',
                      ),
                    ],
                  ),

                  const SizedBox(height: 22),

                  // Soldes par Canal Mobile Money
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceVariant,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Soldes par Canal Mobile Money',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 16),
                        ...data.soldeParCanal.entries.map((entry) {
                          final canal = entry.key;
                          final amount = entry.value;
                          final color = AppColors.getChannelColor(canal);
                          final percent = data.soldeTotal > 0
                              ? (amount / data.soldeTotal).clamp(0.0, 1.0)
                              : 0.0;

                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Row(
                                      children: [
                                        Container(
                                          width: 10,
                                          height: 10,
                                          decoration: BoxDecoration(
                                            color: color,
                                            shape: BoxShape.circle,
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          canal,
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w600,
                                            fontSize: 13,
                                            color: AppColors.textPrimary,
                                          ),
                                        ),
                                      ],
                                    ),
                                    Text(
                                      Formatters.formatFcfa(amount),
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 13,
                                        color: AppColors.textPrimary,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(6),
                                  child: LinearProgressIndicator(
                                    value: percent,
                                    backgroundColor: AppColors.borderLight,
                                    valueColor: AlwaysStoppedAnimation<Color>(color),
                                    minHeight: 6,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Bannière Action Démo Live : Upload Reçu
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.accent.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.accent.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppColors.accent,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.camera_alt, color: AppColors.textPrimary, size: 24),
                        ),
                        const SizedBox(width: 14),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Nouveau paiement Mobile Money ?',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              Text(
                                'Photographiez le SMS ou reçu pour réconciliation IA.',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        ElevatedButton(
                          onPressed: () => context.go('/upload'),
                          child: const Text('Scanner'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _DashboardSkeleton extends StatelessWidget {
  const _DashboardSkeleton();

  @override
  Widget build(BuildContext context) {
    Widget bar({double h = 14}) {
      return Container(
        height: h,
        width: w,
        decoration: BoxDecoration(
          color: AppColors.border,
          borderRadius: BorderRadius.circular(8),
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            height: 128,
            decoration: BoxDecoration(
              color: AppColors.primaryDark.withValues(alpha: 0.88),
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: bar(h: 88)),
              const SizedBox(width: 12),
              Expanded(child: bar(h: 88)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: bar(h: 88)),
              const SizedBox(width: 12),
              Expanded(child: bar(h: 88)),
            ],
          ),
        ],
      ),
    );
  }
}
