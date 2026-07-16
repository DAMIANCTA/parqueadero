import 'package:flutter/material.dart';

class UceParkColors {
  static const navy = Color(0xFF15294D);
  static const maroon = Color(0xFF7A1F2E);
  static const paper = Color(0xFFF5F1E8);
  static const ink = Color(0xFF22252B);
  static const success = Color(0xFF2F7D4F);
  static const danger = Color(0xFFB23B30);
  static const biometric = Color(0xFF5B4B8A);
  static const borderSoft = Color(0xFFD8DAE0);
  static const card = Color(0xFFFFFFFF);
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
      fontFamily: 'Calibri',
    );

    TextStyle titleStyle(double size, [FontWeight weight = FontWeight.w700]) {
      return TextStyle(
        fontFamily: 'Century Schoolbook',
        fontFamilyFallback: const ['Georgia', 'Times New Roman', 'serif'],
        fontSize: size,
        fontWeight: weight,
        color: UceParkColors.navy,
        letterSpacing: 0,
      );
    }

    TextStyle bodyStyle(double size, [FontWeight weight = FontWeight.w400]) {
      return TextStyle(
        fontFamily: 'Calibri',
        fontFamilyFallback: const ['Arial', 'Helvetica', 'sans-serif'],
        fontSize: size,
        fontWeight: weight,
        color: UceParkColors.ink,
        letterSpacing: 0,
      );
    }

    return base.copyWith(
      textTheme: TextTheme(
        headlineLarge: titleStyle(30),
        headlineMedium: titleStyle(26),
        headlineSmall: titleStyle(22),
        titleLarge: titleStyle(20),
        titleMedium: titleStyle(18, FontWeight.w600),
        titleSmall: titleStyle(16, FontWeight.w600),
        bodyLarge: bodyStyle(16),
        bodyMedium: bodyStyle(14),
        bodySmall: bodyStyle(12),
        labelLarge: bodyStyle(15, FontWeight.w600),
        labelMedium: bodyStyle(13, FontWeight.w600),
        labelSmall: bodyStyle(12, FontWeight.w600),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: UceParkColors.navy,
        foregroundColor: Colors.white,
        centerTitle: false,
        elevation: 0,
        titleTextStyle: titleStyle(20).copyWith(color: Colors.white),
      ),
      cardTheme: CardThemeData(
        color: UceParkColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: UceParkColors.borderSoft),
        ),
        margin: EdgeInsets.zero,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: UceParkColors.navy,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: bodyStyle(15, FontWeight.w700),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: UceParkColors.maroon,
          side: const BorderSide(color: UceParkColors.maroon),
          minimumSize: const Size.fromHeight(48),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: bodyStyle(15, FontWeight.w700),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: UceParkColors.card,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        labelStyle:
            bodyStyle(14, FontWeight.w600).copyWith(color: UceParkColors.navy),
        helperStyle: bodyStyle(12)
            .copyWith(color: UceParkColors.ink.withValues(alpha: 0.72)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: UceParkColors.borderSoft),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: UceParkColors.borderSoft),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: UceParkColors.navy, width: 1.4),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: UceParkColors.danger),
        ),
      ),
      dividerColor: UceParkColors.borderSoft,
      snackBarTheme: SnackBarThemeData(
        backgroundColor: UceParkColors.navy,
        contentTextStyle: bodyStyle(14).copyWith(color: Colors.white),
      ),
    );
  }
}
