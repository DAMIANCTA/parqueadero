import 'package:flutter/material.dart';

/// Encabezado de marca UCEPark.
///
/// `compact: false` (login, pantallas de bienvenida): usa el logo "lockup"
/// completo (ya incluye el wordmark "UCEPark" y el subtitulo institucional
/// dibujados en la propia imagen), sin texto adicional al lado.
///
/// `compact: true` (barras internas: hub, historial, setup, etc.): usa solo
/// la marca "P" junto a un wordmark de texto + subtitulo configurable, igual
/// al patron de `UceTopBar` del mockup de referencia.
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
    if (!compact) {
      return Column(
        crossAxisAlignment:
            centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
        children: [
          Image.asset(
            'assets/images/logo_lockup.png',
            width: 200,
            fit: BoxFit.contain,
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(
              subtitle!,
              textAlign: centered ? TextAlign.center : TextAlign.start,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ],
      );
    }

    final textTheme = Theme.of(context).textTheme;
    return Row(
      mainAxisAlignment:
          centered ? MainAxisAlignment.center : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Image.asset('assets/images/logo_mark.png', width: 44, height: 44),
        const SizedBox(width: 12),
        Flexible(
          child: Column(
            crossAxisAlignment:
                centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
            children: [
              Text('UCEPark', style: textTheme.headlineSmall),
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
