import 'package:flutter/material.dart';

import '../theme/ucepark_theme.dart';

/// Widgets compartidos del estilo UCEPark, portados de ucepark_flutter
/// (mockup de referencia) y adaptados al theme ya existente en esta app.

/// Tarjeta blanca redondeada con sombra suave.
class UceCard extends StatelessWidget {
  const UceCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.color,
    this.shadow = true,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? color;
  final bool shadow;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: shadow
            ? [
                BoxShadow(
                  color: const Color(0xFF14284B).withValues(alpha: 0.06),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: child,
    );
  }
}

/// Barra superior con logo (marca) + wordmark "UCEPark", boton de volver
/// opcional y un widget trailing opcional (ej. GateBadge).
class UceTopBar extends StatelessWidget {
  const UceTopBar({
    super.key,
    this.trailing,
    this.showBack = false,
    this.onBack,
  });

  final Widget? trailing;
  final bool showBack;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    final brand = Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Image.asset('assets/images/logo_mark.png', height: 34),
        const SizedBox(width: 7),
        RichText(
          text: const TextSpan(
            style: TextStyle(fontSize: 20, color: UceParkColors.navy),
            children: [
              TextSpan(
                  text: 'UCE', style: TextStyle(fontWeight: FontWeight.w800)),
              TextSpan(
                  text: 'Park', style: TextStyle(fontWeight: FontWeight.w400)),
            ],
          ),
        ),
      ],
    );

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        if (showBack)
          _BackButtonBox(
              onTap: onBack ?? () => Navigator.of(context).maybePop())
        else
          const SizedBox(width: 36),
        brand,
        SizedBox(width: trailing == null ? 36 : null, child: trailing),
      ],
    );
  }
}

class _BackButtonBox extends StatelessWidget {
  const _BackButtonBox({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: UceParkColors.line),
        ),
        child:
            const Icon(Icons.chevron_left, color: UceParkColors.navy, size: 22),
      ),
    );
  }
}

/// Chip azul compacto, usado para mostrar el host MQTT/API configurado.
class GateBadge extends StatelessWidget {
  const GateBadge({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFFE7EEFB),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: UceParkColors.blue,
        ),
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
}

/// Insignia pequeña de estado (verde, roja, ámbar o azul).
class StatusBadge extends StatelessWidget {
  const StatusBadge({
    super.key,
    required this.label,
    required this.bg,
    required this.fg,
  });
  const StatusBadge.green(this.label, {super.key})
      : bg = UceParkColors.successBg,
        fg = UceParkColors.successDark;
  const StatusBadge.red(this.label, {super.key})
      : bg = UceParkColors.dangerBg,
        fg = UceParkColors.dangerDark;
  const StatusBadge.amber(this.label, {super.key})
      : bg = UceParkColors.amberBg,
        fg = UceParkColors.amberDark;
  const StatusBadge.blue(this.label, {super.key})
      : bg = const Color(0xFFE7EEFB),
        fg = UceParkColors.blue;

  final String label;
  final Color bg;
  final Color fg;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
      decoration:
          BoxDecoration(color: bg, borderRadius: BorderRadius.circular(10)),
      child: Text(
        label,
        style:
            TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: fg),
      ),
    );
  }
}

/// Encabezado "hero" para pantallas de resultado (Acceso Permitido/Denegado):
/// circulo grande con icono + titulo + descripcion, sobre fondo tintado.
class UceHero extends StatelessWidget {
  const UceHero({
    super.key,
    required this.authorized,
    required this.title,
    required this.description,
    this.detailChip,
  });

  final bool authorized;
  final String title;
  final String description;
  final String? detailChip;

  @override
  Widget build(BuildContext context) {
    final bg = authorized ? UceParkColors.successBg : UceParkColors.dangerBg;
    final accent = authorized ? UceParkColors.success : UceParkColors.danger;
    final dark =
        authorized ? UceParkColors.successDark : UceParkColors.dangerDark;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 18),
      decoration:
          BoxDecoration(color: bg, borderRadius: BorderRadius.circular(24)),
      child: Column(
        children: [
          Container(
            width: 92,
            height: 92,
            decoration: BoxDecoration(
              color: accent,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: accent.withValues(alpha: 0.4),
                  blurRadius: 18,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Icon(authorized ? Icons.check : Icons.close,
                color: Colors.white, size: 52),
          ),
          const SizedBox(height: 14),
          Text(
            title,
            textAlign: TextAlign.center,
            style: TextStyle(
                fontSize: 32, fontWeight: FontWeight.w800, color: dark),
          ),
          const SizedBox(height: 6),
          Text(
            description,
            textAlign: TextAlign.center,
            style: const TextStyle(
                fontSize: 15, color: Color(0xFF51617C), height: 1.45),
          ),
          if (detailChip != null && detailChip!.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(
                detailChip!,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: UceParkColors.navy,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
