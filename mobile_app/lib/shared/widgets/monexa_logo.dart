import 'package:flutter/material.dart';
import 'package:monexa/core/constants/app_constants.dart';

/// Wordmark officiel MoneXa (`Logos/MONEXA_Fond_Blanc.png`).
class MonexaLogo extends StatelessWidget {
  const MonexaLogo({
    super.key,
    this.height = 44,
    this.alignment = Alignment.center,
  });

  final double height;
  final Alignment alignment;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'MONEXA',
      image: true,
      child: Image.asset(
        AppConstants.logoAsset,
        height: height,
        fit: BoxFit.contain,
        alignment: alignment,
        filterQuality: FilterQuality.high,
      ),
    );
  }
}
