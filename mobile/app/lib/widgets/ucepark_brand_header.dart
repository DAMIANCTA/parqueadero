import 'package:flutter/material.dart';

class UceParkBrandHeader extends StatelessWidget {
  const UceParkBrandHeader({
    super.key,
    this.compact = false,
    this.centered = false,
    this.subtitle,
  });

  final bool compact;
  final bool centered;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final logoSize = compact ? 64.0 : 96.0;

    return Row(
      mainAxisAlignment:
          centered ? MainAxisAlignment.center : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Image.asset(
          'assets/images/ucepark_logo.png',
          width: logoSize,
          height: logoSize,
          fit: BoxFit.contain,
        ),
        const SizedBox(width: 14),
        Flexible(
          child: Column(
            crossAxisAlignment:
                centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
            children: [
              Text(
                'UCEPark',
                style: compact
                    ? textTheme.headlineSmall
                    : textTheme.headlineMedium,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle ?? 'Universidad Central del Ecuador',
                style: textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
