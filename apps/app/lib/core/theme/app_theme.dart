import 'package:flutter/material.dart';

import 'fonts.dart';
import 'sn_colors.dart';
import 'tokens.g.dart';

/// Light Material 3 theme, built only from generated design tokens.
ThemeData buildAppTheme() => _build(SnColors.light, Brightness.light);

/// Dark Material 3 theme, built only from generated design tokens.
ThemeData buildDarkAppTheme() => _build(SnColors.dark, Brightness.dark);

/// Minimum touch height for buttons: older users on low-end phones.
const double _buttonHeight = SnTokens.space7 + SnTokens.space1;

ThemeData _build(SnColors c, Brightness brightness) {
  // The brand accent seeds the scheme; verdict colours never come from it
  // (they live in verdict_colors.dart), and nothing in it is green.
  final scheme =
      ColorScheme.fromSeed(seedColor: c.brand, brightness: brightness).copyWith(
        primary: c.brand,
        onPrimary: c.textInverse,
        primaryContainer: c.brandSoft,
        onPrimaryContainer: c.brandStrong,
        secondary: c.brandStrong,
        onSecondary: c.textInverse,
        secondaryContainer: c.brandSoft,
        onSecondaryContainer: c.brandStrong,
        surface: c.surface,
        onSurface: c.textPrimary,
        onSurfaceVariant: c.textSecondary,
        surfaceTint: c.brand,
        surfaceContainerLowest: c.surface,
        surfaceContainerLow: c.surface,
        surfaceContainer: c.canvas,
        surfaceContainerHigh: c.muted,
        surfaceContainerHighest: c.muted,
        outline: c.borderStrong,
        outlineVariant: c.border,
        error: c.verdictAvoid,
        onError: c.onVerdict,
        errorContainer: c.verdictAvoidSurface,
        onErrorContainer: c.textPrimary,
      );

  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    fontFamily: snFontFamily,
  ).textTheme;
  // Devanagari needs more line height than Latin for its matras.
  TextStyle? style(TextStyle? s, double size, FontWeight w, double height) =>
      s?.copyWith(
        fontSize: size,
        fontWeight: w,
        height: height,
        letterSpacing: 0,
      );
  final textTheme = base
      .copyWith(
        displaySmall: style(
          base.displaySmall,
          SnTokens.fontSize3xl,
          FontWeight.w700,
          1.2,
        ),
        headlineMedium: style(
          base.headlineMedium,
          SnTokens.fontSize2xl,
          FontWeight.w700,
          1.25,
        ),
        headlineSmall: style(
          base.headlineSmall,
          SnTokens.fontSizeXl,
          FontWeight.w700,
          1.3,
        ),
        titleLarge: style(
          base.titleLarge,
          SnTokens.fontSizeLg,
          FontWeight.w700,
          1.3,
        ),
        titleMedium: style(
          base.titleMedium,
          SnTokens.fontSizeMd,
          FontWeight.w600,
          1.35,
        ),
        titleSmall: style(
          base.titleSmall,
          SnTokens.fontSizeSm,
          FontWeight.w600,
          1.35,
        ),
        bodyLarge: style(
          base.bodyLarge,
          SnTokens.fontSizeMd,
          FontWeight.w400,
          1.45,
        ),
        bodyMedium: style(
          base.bodyMedium,
          SnTokens.fontSizeMd,
          FontWeight.w400,
          1.45,
        ),
        bodySmall: style(
          base.bodySmall,
          SnTokens.fontSizeSm,
          FontWeight.w400,
          1.4,
        ),
        labelLarge: style(
          base.labelLarge,
          SnTokens.fontSizeMd,
          FontWeight.w600,
          1.2,
        ),
        labelMedium: style(
          base.labelMedium,
          SnTokens.fontSizeSm,
          FontWeight.w600,
          1.2,
        ),
        labelSmall: style(
          base.labelSmall,
          SnTokens.fontSizeXs,
          FontWeight.w600,
          1.2,
        ),
      )
      .apply(bodyColor: c.textPrimary, displayColor: c.textPrimary);

  final buttonShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.circular(SnTokens.radiusLg),
  );
  const buttonPadding = EdgeInsets.symmetric(
    horizontal: SnTokens.space5,
    vertical: SnTokens.space3,
  );
  final inputRadius = BorderRadius.circular(
    SnTokens.radiusMd + SnTokens.space1,
  );
  OutlineInputBorder inputBorder(Color color, [double width = 1]) =>
      OutlineInputBorder(
        borderRadius: inputRadius,
        borderSide: BorderSide(color: color, width: width),
      );

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    fontFamily: snFontFamily,
    textTheme: textTheme,
    scaffoldBackgroundColor: c.canvas,
    canvasColor: c.canvas,
    dividerColor: c.border,
    extensions: [c],
    visualDensity: VisualDensity.standard,
    appBarTheme: AppBarTheme(
      backgroundColor: c.canvas,
      foregroundColor: c.textPrimary,
      surfaceTintColor: c.canvas,
      elevation: SnTokens.elevationNone,
      scrolledUnderElevation: SnTokens.elevationLow,
      centerTitle: false,
      titleTextStyle: textTheme.titleLarge,
    ),
    cardTheme: CardThemeData(
      color: c.surface,
      surfaceTintColor: c.surface,
      elevation: SnTokens.elevationNone,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(SnTokens.radiusLg),
        side: BorderSide(color: c.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: c.brand,
        foregroundColor: c.textInverse,
        disabledBackgroundColor: c.muted,
        disabledForegroundColor: c.textSecondary,
        minimumSize: const Size(_buttonHeight, _buttonHeight),
        padding: buttonPadding,
        shape: buttonShape,
        textStyle: textTheme.labelLarge,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: c.brand,
        backgroundColor: c.surface,
        minimumSize: const Size(_buttonHeight, _buttonHeight),
        padding: buttonPadding,
        shape: buttonShape,
        side: BorderSide(color: c.borderStrong),
        textStyle: textTheme.labelLarge,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: c.brand,
        minimumSize: const Size(SnTokens.space7, SnTokens.space7),
        padding: const EdgeInsets.symmetric(horizontal: SnTokens.space3),
        textStyle: textTheme.labelLarge,
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(foregroundColor: c.textSecondary),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: c.surface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space4,
        vertical: SnTokens.space3 + SnTokens.space1,
      ),
      border: inputBorder(c.borderStrong),
      enabledBorder: inputBorder(c.borderStrong),
      disabledBorder: inputBorder(c.border),
      focusedBorder: inputBorder(c.brand, 2),
      errorBorder: inputBorder(c.verdictAvoid),
      focusedErrorBorder: inputBorder(c.verdictAvoid, 2),
      labelStyle: textTheme.bodyMedium?.copyWith(color: c.textSecondary),
      hintStyle: textTheme.bodyMedium?.copyWith(color: c.textSecondary),
      errorStyle: textTheme.bodySmall?.copyWith(color: c.verdictAvoid),
      errorMaxLines: 3,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: c.surface,
      selectedColor: c.brandSoft,
      disabledColor: c.muted,
      checkmarkColor: c.brandStrong,
      labelStyle: textTheme.labelMedium?.copyWith(color: c.textPrimary),
      secondaryLabelStyle: textTheme.labelMedium?.copyWith(
        color: c.brandStrong,
      ),
      side: BorderSide(color: c.borderStrong),
      shape: const StadiumBorder(),
      padding: const EdgeInsets.symmetric(
        horizontal: SnTokens.space2,
        vertical: SnTokens.space1,
      ),
    ),
    checkboxTheme: CheckboxThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(SnTokens.radiusSm),
      ),
      side: BorderSide(color: c.borderStrong, width: 2),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: c.surface,
      surfaceTintColor: c.surface,
      indicatorColor: c.brandSoft,
      elevation: SnTokens.elevationMedium,
      height: SnTokens.space8 + SnTokens.space2,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => textTheme.labelSmall?.copyWith(
          fontSize: SnTokens.fontSizeXs,
          color: states.contains(WidgetState.selected)
              ? c.brandStrong
              : c.textSecondary,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected)
              ? c.brandStrong
              : c.textSecondary,
        ),
      ),
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(
      color: c.brand,
      linearTrackColor: c.brandSoft,
      circularTrackColor: c.brandSoft,
    ),
    dividerTheme: DividerThemeData(
      color: c.border,
      thickness: 1,
      space: SnTokens.space4,
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(SnTokens.radiusMd),
      ),
    ),
    listTileTheme: ListTileThemeData(
      iconColor: c.textSecondary,
      textColor: c.textPrimary,
    ),
  );
}
