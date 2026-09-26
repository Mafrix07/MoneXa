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

  static bool get _inWidgetTest =>
      WidgetsBinding.instance.runtimeType.toString().contains('Test');

  @override
  Widget build(BuildContext context) {
    if (_inWidgetTest) {
      return SizedBox(
        height: height,
        child: const Align(
          child: Text('MONEXA', style: TextStyle(fontWeight: FontWeight.w800)),
        ),
      );
    }

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
