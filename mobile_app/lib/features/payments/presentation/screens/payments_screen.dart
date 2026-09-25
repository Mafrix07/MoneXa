import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:monexa/core/theme/app_colors.dart';
import 'package:monexa/shared/utils/formatters.dart';
import 'package:monexa/shared/widgets/status_badge.dart';
import 'package:monexa/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:monexa/features/payments/presentation/bloc/payments_bloc.dart';
import 'package:monexa/features/payments/data/payment_repository.dart';

class PaymentsScreen extends StatefulWidget {
  const PaymentsScreen({super.key});

  @override
  State<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends State<PaymentsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<String> _filters = ['TOUS', 'A_VALIDER', 'RECONCILIE', 'ANOMALIE'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _filters.length, vsync: this);
    context.read<PaymentsBloc>().add(LoadPaymentsEvent(status: 'TOUS'));

    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        final selected = _filters[_tabController.index];
        context.read<PaymentsBloc>().add(LoadPaymentsEvent(status: selected));
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthBloc>().state;
    bool canValidate = false;
    if (authState is Authenticated) {
      canValidate = authState.user.role == 'GERANT' || authState.user.role == 'COMPTABLE';
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Historique des Paiements'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.accent,
          indicatorWeight: 3,
          tabs: const [
            Tab(text: 'Tous'),
            Tab(text: 'À Valider'),
            Tab(text: 'Réconciliés'),
            Tab(text: 'Anomalies'),
          ],
        ),
      ),
      body: BlocBuilder<PaymentsBloc, PaymentsState>(
        builder: (context, state) {
          if (state is PaymentsLoading) {
            return const Center(
              child: CircularProgressIndicator(color: AppColors.primary),
            );
          }

          if (state is PaymentsError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline_rounded, size: 48, color: AppColors.destructive),
                    const SizedBox(height: 12),
                    Text(state.message, textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        final selected = _filters[_tabController.index];
                        context.read<PaymentsBloc>().add(LoadPaymentsEvent(status: selected));
                      },
                      child: const Text('Réessayer'),
                    ),
                  ],
                ),
              ),
            );
          }

          if (state is! PaymentsLoaded) {
            return const SizedBox.shrink();
          }

          final payments = state.payments;

          if (payments.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.inbox_outlined, size: 56, color: AppColors.textMuted.withValues(alpha: 0.5)),
                  const SizedBox(height: 12),
                  const Text(
                    'Aucun paiement dans cette catégorie.',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () async {
              final selected = _filters[_tabController.index];
              context.read<PaymentsBloc>().add(LoadPaymentsEvent(status: selected));
            },
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: payments.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final payment = payments[index];
                return _buildPaymentCard(context, payment, canValidate);
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildPaymentCard(BuildContext context, PaymentItem payment, bool canValidate) {
    final channelColor = AppColors.getChannelColor(payment.channel);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // En-tête : Canal, Statut et Date
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: channelColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.phone_android_rounded, size: 16, color: channelColor),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    payment.channel,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: channelColor,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              StatusBadge(status: payment.status),
            ],
          ),

          const SizedBox(height: 12),

          // Ligne Montant et Payeur
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      payment.payerName,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    if (payment.payerPhone.isNotEmpty)
                      Text(
                        payment.payerPhone,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                  ],
                ),
              ),
              Text(
                Formatters.formatFcfa(payment.amount),
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),
          const Divider(height: 12, color: AppColors.borderLight),

          // Métadonnées : Référence, matching et date
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Réf : ${payment.providerRef}',
                    style: const TextStyle(
                      fontSize: 11,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.w600,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  if (payment.invoiceRef != null)
                    Text(
                      'Facture : ${payment.invoiceRef}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.success,
                      ),
                    ),
                ],
              ),
              Text(
                Formatters.formatDateTime(payment.paidAt),
                style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
              ),
            ],
          ),

          // Actions de validation pour le comptable / gérant si À VALIDER
          if (payment.status == 'A_VALIDER' && canValidate) ...[
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.destructive,
                      side: const BorderSide(color: AppColors.destructive),
                      padding: const EdgeInsets.symmetric(vertical: 8),
                    ),
                    icon: const Icon(Icons.close, size: 16),
                    label: const Text('Rejeter', style: TextStyle(fontSize: 12)),
                    onPressed: () {
                      context.read<PaymentsBloc>().add(
                            ValidatePaymentActionSubmittedEvent(
                              paymentId: payment.id,
                              action: 'REJECT',
                              currentFilterStatus: _filters[_tabController.index],
                            ),
                          );
                    },
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.success,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                    ),
                    icon: const Icon(Icons.check, size: 16),
                    label: const Text('Valider', style: TextStyle(fontSize: 12)),
                    onPressed: () {
                      context.read<PaymentsBloc>().add(
                            ValidatePaymentActionSubmittedEvent(
                              paymentId: payment.id,
                              action: 'APPROVE',
                              currentFilterStatus: _filters[_tabController.index],
                            ),
                          );
                    },
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
