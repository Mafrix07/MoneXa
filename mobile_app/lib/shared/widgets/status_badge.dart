import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final bool isChannel;

  const StatusBadge({
    super.key,
    required this.status,
    this.isChannel = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = isChannel
        ? AppColors.getChannelColor(status)
        : AppColors.getStatusColor(status);

    String label = status;
    if (!isChannel) {
      switch (status.toUpperCase()) {
        case 'RECONCILIE':
          label = 'Réconcilié';
          break;
        case 'A_VALIDER':
          label = 'À valider';
          break;
        case 'ANOMALIE':
          label = 'Anomalie';
          break;
        case 'NON_RATTACHE':
          label = 'Non rattaché';
          break;
      }
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3), width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
