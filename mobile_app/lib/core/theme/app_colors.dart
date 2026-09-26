import 'package:flutter/material.dart';

/// Palette MoneXa — indigo, or, mist. Alignée sur DESIGN.md.
class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF063082);
  static const Color primaryDark = Color(0xFF0B1F4D);
  static const Color primaryLight = Color(0xFF1D4ED8);

  static const Color textPrimary = Color(0xFF0B1F4D);
  static const Color textSecondary = Color(0xFF4A5A73);
  static const Color textMuted = Color(0xFF8A97AB);

  static const Color background = Color(0xFFF4F6F8);
  static const Color surface = Color(0xFFF7F8FB);
  static const Color surfaceVariant = Color(0xFFFFFFFF);

  static const Color accent = Color(0xFFE08A00);
  static const Color success = Color(0xFF0F6B45);
  static const Color destructive = Color(0xFFB42318);
  static const Color warning = Color(0xFFB45309);
  static const Color info = Color(0xFF1D4ED8);

  static const Color border = Color(0xFFD5DCE8);
  static const Color borderLight = Color(0xFFE4E9F2);

  static const Color channelTMoney = Color(0xFF063082);
  static const Color channelMoov = Color(0xFF0F6B45);
  static const Color channelFlooz = Color(0xFFB45309);
  static const Color channelBanque = Color(0xFF4A5A73);
  static const Color channelEspeces = Color(0xFF3D2B1F);

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
