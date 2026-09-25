import 'package:flutter/material.dart';

/// Palette de couleurs MoneXa — Extraite de code couleur.jpeg et docs/design-system.md
class AppColors {
  AppColors._();

  // Couleurs principales
  static const Color primary = Color(0xFF063082); // Bleu indigo profond
  static const Color primaryDark = Color(0xFF041E54);
  static const Color primaryLight = Color(0xFF1D4ED8);

  static const Color textPrimary = Color(0xFF1A2539); // Marine foncé
  static const Color textSecondary = Color(0xFF64748B); // Gris ardoise
  static const Color textMuted = Color(0xFF9DA9C3); // Gris-bleu

  static const Color background = Color(0xFFFFFBF4); // Crème chaud
  static const Color surface = Colors.white;
  static const Color surfaceVariant = Color(0xFFF8FAFC);

  // Couleurs d'accent et statuts
  static const Color accent = Color(0xFFF59E0B); // Or / CTA
  static const Color success = Color(0xFF059669); // Vert émeraude
  static const Color destructive = Color(0xFFDC2626); // Rouge vif
  static const Color warning = Color(0xFFD97706); // Ambre foncé
  static const Color info = Color(0xFF0284C7); // Bleu ciel

  // Bordures et séparateurs
  static const Color border = Color(0xFFCBD5E1);
  static const Color borderLight = Color(0xFFE2E8F0);

  // Couleurs par canal de paiement
  static const Color channelTMoney = Color(0xFF063082); // Indigo
  static const Color channelMoov = Color(0xFF059669); // Vert émeraude
  static const Color channelFlooz = Color(0xFFF59E0B); // Or
  static const Color channelBanque = Color(0xFF64748B); // Gris ardoise
  static const Color channelEspeces = Color(0xFF2C3E5A); // Marine light

  static Color getChannelColor(String? channel) {
    switch (channel?.toUpperCase()) {
      case 'TMONEY':
      case 'T-MONEY':
        return channelTMoney;
      case 'MOOV':
      case 'MOOV MONEY':
        return channelMoov;
      case 'FLOOZ':
        return channelFlooz;
      case 'BANQUE':
        return channelBanque;
      case 'ESPECES':
        return channelEspeces;
      default:
        return primary;
    }
  }

  static Color getStatusColor(String? status) {
    switch (status?.toUpperCase()) {
      case 'RECONCILIE':
        return success;
      case 'A_VALIDER':
        return accent;
      case 'ANOMALIE':
        return destructive;
      case 'NON_RATTACHE':
      default:
        return textMuted;
    }
  }
}
