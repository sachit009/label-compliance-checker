import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Premium dark theme with glassmorphism effects and gradient accents.
class AppTheme {
  AppTheme._();

  // ── Color Palette ────────────────────────────────────────────
  static const Color background = Color(0xFF0A0E21);
  static const Color surface = Color(0xFF1A1F36);
  static const Color surfaceLight = Color(0xFF252B48);
  static const Color cardDark = Color(0xFF161B33);

  // Accent gradient colors
  static const Color accentPrimary = Color(0xFF6C5CE7);    // Indigo
  static const Color accentSecondary = Color(0xFF00CEC9);  // Teal
  static const Color accentTertiary = Color(0xFFFD79A8);   // Rose

  // Status colors
  static const Color compliant = Color(0xFF00B894);     // Emerald green
  static const Color nonCompliant = Color(0xFFE17055);  // Coral red
  static const Color partial = Color(0xFFFDCB6E);       // Amber gold
  static const Color illegible = Color(0xFFE17055);

  // Text colors
  static const Color textPrimary = Color(0xFFF5F6FA);
  static const Color textSecondary = Color(0xFFA4B0BE);
  static const Color textMuted = Color(0xFF636E82);

  // ── Gradients ────────────────────────────────────────────────
  static const LinearGradient accentGradient = LinearGradient(
    colors: [accentPrimary, accentSecondary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient heroGradient = LinearGradient(
    colors: [
      Color(0xFF6C5CE7),
      Color(0xFF4834D4),
      Color(0xFF00CEC9),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient backgroundGradient = LinearGradient(
    colors: [
      Color(0xFF0A0E21),
      Color(0xFF101530),
      Color(0xFF0A0E21),
    ],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  static LinearGradient statusGradient(String status) {
    switch (status) {
      case 'COMPLIANT':
        return const LinearGradient(
          colors: [Color(0xFF00B894), Color(0xFF00CEC9)],
        );
      case 'NON_COMPLIANT':
        return const LinearGradient(
          colors: [Color(0xFFE17055), Color(0xFFD63031)],
        );
      case 'PARTIALLY_COMPLIANT':
        return const LinearGradient(
          colors: [Color(0xFFFDCB6E), Color(0xFFF39C12)],
        );
      default:
        return accentGradient;
    }
  }

  // ── Glass Effect Decoration ──────────────────────────────────
  static BoxDecoration glassDecoration({
    double opacity = 0.08,
    double borderRadius = 20,
    Color? borderColor,
  }) {
    return BoxDecoration(
      color: Colors.white.withValues(alpha: opacity),
      borderRadius: BorderRadius.circular(borderRadius),
      border: Border.all(
        color: borderColor ?? Colors.white.withValues(alpha: 0.1),
        width: 1,
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.2),
          blurRadius: 20,
          spreadRadius: -5,
        ),
      ],
    );
  }

  static BoxDecoration glassDecorationWithGradient({
    double opacity = 0.05,
    double borderRadius = 20,
    required Gradient gradient,
  }) {
    return BoxDecoration(
      gradient: gradient,
      borderRadius: BorderRadius.circular(borderRadius),
      border: Border.all(
        color: Colors.white.withValues(alpha: 0.1),
        width: 1,
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.3),
          blurRadius: 24,
          spreadRadius: -8,
        ),
      ],
    );
  }

  // ── Theme Data ───────────────────────────────────────────────
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      primaryColor: accentPrimary,
      colorScheme: const ColorScheme.dark(
        primary: accentPrimary,
        secondary: accentSecondary,
        surface: surface,
        error: nonCompliant,
      ),
      textTheme: GoogleFonts.interTextTheme(
        const TextTheme(
          displayLarge: TextStyle(
            fontSize: 32,
            fontWeight: FontWeight.w800,
            color: textPrimary,
            letterSpacing: -1,
          ),
          displayMedium: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w700,
            color: textPrimary,
            letterSpacing: -0.5,
          ),
          headlineMedium: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: textPrimary,
          ),
          titleLarge: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
          titleMedium: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: textPrimary,
          ),
          bodyLarge: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w400,
            color: textSecondary,
          ),
          bodyMedium: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w400,
            color: textSecondary,
          ),
          bodySmall: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w400,
            color: textMuted,
          ),
          labelLarge: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: textPrimary,
            letterSpacing: 0.5,
          ),
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        iconTheme: const IconThemeData(color: textPrimary),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          textStyle: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: surfaceLight,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  // ── Utility: Status Color ────────────────────────────────────
  static Color statusColor(String status) {
    switch (status) {
      case 'COMPLIANT':
      case 'FOUND':
        return compliant;
      case 'NON_COMPLIANT':
      case 'MISSING':
        return nonCompliant;
      case 'PARTIALLY_COMPLIANT':
      case 'ILLEGIBLE':
        return partial;
      default:
        return textMuted;
    }
  }

  static IconData statusIcon(String status) {
    switch (status) {
      case 'COMPLIANT':
      case 'FOUND':
        return Icons.check_circle_rounded;
      case 'NON_COMPLIANT':
      case 'MISSING':
        return Icons.cancel_rounded;
      case 'PARTIALLY_COMPLIANT':
        return Icons.warning_amber_rounded;
      case 'ILLEGIBLE':
        return Icons.visibility_off_rounded;
      default:
        return Icons.help_outline_rounded;
    }
  }

  static String statusLabel(String status) {
    switch (status) {
      case 'COMPLIANT':
        return 'Compliant';
      case 'NON_COMPLIANT':
        return 'Non-Compliant';
      case 'PARTIALLY_COMPLIANT':
        return 'Partially Compliant';
      case 'FOUND':
        return 'Found';
      case 'MISSING':
        return 'Missing';
      case 'ILLEGIBLE':
        return 'Illegible';
      default:
        return status;
    }
  }
}
