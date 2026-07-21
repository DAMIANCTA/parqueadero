import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Paleta UCEPark, alineada al mockup de referencia (ucepark_flutter).
/// Se conservan los nombres ya usados en el resto de la app (navy, maroon,
/// ink, paper, success, danger, biometric, borderSoft, card) para no romper
/// llamadas existentes; los demas son nuevos, portados del mockup.
class UceParkColors {
  static const navy = Color(0xFF1B2F5E);
  static const navy2 = Color(0xFF1D3B6E);
  static const maroon = Color(0xFF7D1F2D);
  static const blue = Color(0xFF2456A6);
  static const ink = Color(0xFF22314A);
  static const muted = Color(0xFF6B7A90);
  static const paper = Color(0xFFF2F4F8);
  static const line = Color(0xFFE6EAF1);
  static const borderSoft = line;
  static const card = Colors.white;
  static const biometric = Color(0xFF5B4B8A);

  static const success = Color(0xFF27A844);
  static const successDark = Color(0xFF1D7A34);
  static const successBg = Color(0xFFE8F6EC);

  static const danger = Color(0xFFE04444);
  static const dangerDark = Color(0xFFB53232);
  static const dangerBg = Color(0xFFFDEAEA);

  static const amber = Color(0xFFE8A13C);
  static const amberDark = Color(0xFFA86A13);
  static const amberBg = Color(0xFFFDF3E3);

  static const chip = Color(0xFFF1F3F6);
  static const scan = Color(0xFF4EE38A);
  static const camDark = Color(0xFF1E2739);
  static const camMid = Color(0xFF2B3550);
}

class UceParkTheme {
  static ThemeData build() {
    const colorScheme = ColorScheme(
      brightness: Brightness.light,
      primary: UceParkColors.navy,
      onPrimary: Colors.white,
      secondary: UceParkColors.maroon,
      onSecondary: Colors.white,
      error: UceParkColors.danger,
      onError: Colors.white,
      surface: UceParkColors.card,
      onSurface: UceParkColors.ink,
      tertiary: UceParkColors.biometric,
      onTertiary: Colors.white,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: UceParkColors.paper,
      primaryColor: UceParkColors.navy,
    );

    final textTheme = GoogleFonts.montserratTextTheme(base.textTheme).apply(
      bodyColor: UceParkColors.ink,
      displayColor: UceParkColors.navy,
    );

    return base.copyWith(
      textTheme: textTheme.copyWith(
        headlineLarge: textTheme.headlineLarge
            ?.copyWith(fontWeight: FontWeight.w800, color: UceParkColors.navy),
        headlineMedium: textTheme.headlineMedium
            ?.copyWith(fontWeight: FontWeight.w800, color: UceParkColors.navy),
        headlineSmall: textTheme.headlineSmall
            ?.copyWith(fontWeight: FontWeight.w800, color: UceParkColors.navy),
        titleLarge: textTheme.titleLarge
            ?.copyWith(fontWeight: FontWeight.w800, color: UceParkColors.navy),
        titleMedium: textTheme.titleMedium
            ?.copyWith(fontWeight: FontWeight.w700, color: UceParkColors.navy),
        titleSmall: textTheme.titleSmall
            ?.copyWith(fontWeight: FontWeight.w700, color: UceParkColors.navy),
        labelLarge: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w700),
        labelMedium:
            textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w700),
        labelSmall: textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w700),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: UceParkColors.navy,
        foregroundColor: Colors.white,
        centerTitle: false,
        elevation: 0,
        titleTextStyle: GoogleFonts.montserrat(
          fontSize: 20,
          fontWeight: FontWeight.w800,
          color: Colors.white,
        ),
      ),
      cardTheme: CardThemeData(
        color: UceParkColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide.none,
        ),
        margin: EdgeInsets.zero,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: UceParkColors.navy2,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: GoogleFonts.montserrat(
              fontSize: 15.5, fontWeight: FontWeight.w800),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: UceParkColors.navy,
          backgroundColor: Colors.white,
          side: const BorderSide(color: UceParkColors.line, width: 1.5),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle:
              GoogleFonts.montserrat(fontSize: 15, fontWeight: FontWeight.w700),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: UceParkColors.navy,
          textStyle: GoogleFonts.montserrat(fontWeight: FontWeight.w700),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        labelStyle:
            GoogleFonts.montserrat(fontSize: 13, fontWeight: FontWeight.w700)
                .copyWith(color: UceParkColors.navy),
        helperStyle: GoogleFonts.montserrat(fontSize: 12)
            .copyWith(color: UceParkColors.ink.withValues(alpha: 0.72)),
        hintStyle: GoogleFonts.montserrat(color: const Color(0xFF9AA7B8)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(13),
          borderSide: const BorderSide(color: UceParkColors.line, width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(13),
          borderSide: const BorderSide(color: UceParkColors.line, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(13),
          borderSide: const BorderSide(color: UceParkColors.blue, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(13),
          borderSide: const BorderSide(color: UceParkColors.danger),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: Colors.white,
        selectedColor: UceParkColors.navy2,
        labelStyle: GoogleFonts.montserrat(
            fontSize: 12.5,
            fontWeight: FontWeight.w700,
            color: UceParkColors.ink),
        secondaryLabelStyle: GoogleFonts.montserrat(
            fontSize: 12.5, fontWeight: FontWeight.w700, color: Colors.white),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: UceParkColors.line, width: 1.5),
        ),
      ),
      dividerColor: UceParkColors.line,
      snackBarTheme: SnackBarThemeData(
        backgroundColor: UceParkColors.navy,
        contentTextStyle:
            GoogleFonts.montserrat(fontSize: 14, color: Colors.white),
      ),
    );
  }
}
