import 'package:flutter/material.dart';

import 'tokens.g.dart';

/// Material theme built only from generated design tokens.
ThemeData buildAppTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: SnTokens.gradeA,
    surface: SnTokens.surfaceDefault,
    onSurface: SnTokens.textPrimary,
    error: SnTokens.verdictAvoid,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: SnTokens.surfaceDefault,
    textTheme: ThemeData.light().textTheme.apply(
      bodyColor: SnTokens.textPrimary,
      displayColor: SnTokens.textPrimary,
    ),
  );
}
