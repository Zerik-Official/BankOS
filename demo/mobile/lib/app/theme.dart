import 'package:flutter/material.dart';

/// Visual theme of the app, built from the BankOS brand colors.
abstract final class AppTheme {
  /// Main brand purple, used for the selected items and the highlighted actions.
  static const Color brandPurple = Color(0xFF6A00D4);

  /// Deep purple used for the wordmark and the dark header.
  static const Color brandDeep = Color(0xFF3F0072);

  /// Almost black purple used for the bottom navigation bar.
  static const Color brandNight = Color(0xFF1A0B2E);

  /// Light lavender used as the page background.
  static const Color brandLavender = Color(0xFFF6F2FF);

  /// Soft lavender used for icon containers and secondary buttons.
  static const Color brandSoft = Color(0xFFEDE4FF);

  /// Light theme used by the whole app.
  static ThemeData light() {
    final ColorScheme scheme = ColorScheme.fromSeed(seedColor: brandPurple)
        .copyWith(
          primary: brandPurple,
          onPrimary: Colors.white,
          primaryContainer: brandSoft,
          onPrimaryContainer: brandDeep,
          surface: Colors.white,
          surfaceTint: Colors.transparent,
        );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: brandLavender,
      appBarTheme: const AppBarTheme(
        backgroundColor: brandPurple,
        foregroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: Colors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(64, 52),
          shape: const StadiumBorder(),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: brandPurple, width: 1.5),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: brandNight,
        surfaceTintColor: Colors.transparent,
        indicatorColor: brandPurple,
        iconTheme: WidgetStateProperty.resolveWith((Set<WidgetState> states) {
          final bool selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? Colors.white : Colors.white70);
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((
          Set<WidgetState> states,
        ) {
          final bool selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? Colors.white : Colors.white70,
          );
        }),
      ),
    );
  }
}
