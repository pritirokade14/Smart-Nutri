import 'package:flutter/material.dart';

import 'tokens.g.dart';

/// Semantic colours that change between the light and dark themes, built only
/// from the generated design tokens. Widgets read them with
/// `SnColors.of(context)`; outside an app theme (e.g. a bare test harness)
/// the light palette is used.
@immutable
class SnColors extends ThemeExtension<SnColors> {
  const SnColors({
    required this.canvas,
    required this.surface,
    required this.muted,
    required this.border,
    required this.borderStrong,
    required this.textPrimary,
    required this.textSecondary,
    required this.textInverse,
    required this.brand,
    required this.brandSoft,
    required this.brandStrong,
    required this.accentWarm,
    required this.accentPeach,
    required this.verdictOk,
    required this.verdictCaution,
    required this.verdictAvoid,
    required this.verdictUnknown,
    required this.verdictOkSurface,
    required this.verdictCautionSurface,
    required this.verdictAvoidSurface,
    required this.verdictUnknownSurface,
    required this.onVerdict,
    required this.googleSurface,
    required this.googleBorder,
    required this.googleText,
  });

  static const light = SnColors(
    canvas: SnTokens.surfaceCanvas,
    surface: SnTokens.surfaceDefault,
    muted: SnTokens.surfaceMuted,
    border: SnTokens.borderDefault,
    borderStrong: SnTokens.borderStrong,
    textPrimary: SnTokens.textPrimary,
    textSecondary: SnTokens.textSecondary,
    textInverse: SnTokens.textInverse,
    brand: SnTokens.brandPrimary,
    brandSoft: SnTokens.brandSoft,
    brandStrong: SnTokens.brandStrong,
    accentWarm: SnTokens.accentWarm,
    accentPeach: SnTokens.accentPeach,
    verdictOk: SnTokens.verdictOk,
    verdictCaution: SnTokens.verdictCaution,
    verdictAvoid: SnTokens.verdictAvoid,
    verdictUnknown: SnTokens.verdictUnknown,
    verdictOkSurface: SnTokens.surfaceVerdictOk,
    verdictCautionSurface: SnTokens.surfaceVerdictCaution,
    verdictAvoidSurface: SnTokens.surfaceVerdictAvoid,
    verdictUnknownSurface: SnTokens.surfaceVerdictUnknown,
    onVerdict: SnTokens.textInverse,
    googleSurface: SnTokens.googleSurface,
    googleBorder: SnTokens.googleBorder,
    googleText: SnTokens.googleText,
  );

  static const dark = SnColors(
    canvas: SnTokens.darkSurfaceCanvas,
    surface: SnTokens.darkSurfaceDefault,
    muted: SnTokens.darkSurfaceMuted,
    border: SnTokens.darkBorderDefault,
    borderStrong: SnTokens.darkBorderStrong,
    textPrimary: SnTokens.darkTextPrimary,
    textSecondary: SnTokens.darkTextSecondary,
    textInverse: SnTokens.darkTextInverse,
    brand: SnTokens.darkBrandPrimary,
    brandSoft: SnTokens.darkBrandSoft,
    brandStrong: SnTokens.darkBrandStrong,
    accentWarm: SnTokens.accentWarm,
    accentPeach: SnTokens.darkBrandSoft,
    verdictOk: SnTokens.darkVerdictOk,
    verdictCaution: SnTokens.darkVerdictCaution,
    verdictAvoid: SnTokens.darkVerdictAvoid,
    verdictUnknown: SnTokens.darkVerdictUnknown,
    verdictOkSurface: SnTokens.darkSurfaceVerdictOk,
    verdictCautionSurface: SnTokens.darkSurfaceVerdictCaution,
    verdictAvoidSurface: SnTokens.darkSurfaceVerdictAvoid,
    verdictUnknownSurface: SnTokens.darkSurfaceVerdictUnknown,
    onVerdict: SnTokens.darkTextInverse,
    googleSurface: SnTokens.darkGoogleSurface,
    googleBorder: SnTokens.darkGoogleBorder,
    googleText: SnTokens.darkGoogleText,
  );

  static SnColors of(BuildContext context) =>
      Theme.of(context).extension<SnColors>() ?? light;

  final Color canvas;
  final Color surface;
  final Color muted;
  final Color border;
  final Color borderStrong;
  final Color textPrimary;
  final Color textSecondary;
  final Color textInverse;
  final Color brand;
  final Color brandSoft;
  final Color brandStrong;
  final Color accentWarm;
  final Color accentPeach;
  final Color verdictOk;
  final Color verdictCaution;
  final Color verdictAvoid;
  final Color verdictUnknown;
  final Color verdictOkSurface;
  final Color verdictCautionSurface;
  final Color verdictAvoidSurface;
  final Color verdictUnknownSurface;

  /// Text and icons drawn on a solid verdict colour.
  final Color onVerdict;
  final Color googleSurface;
  final Color googleBorder;
  final Color googleText;

  @override
  SnColors copyWith() => this;

  /// Palettes switch with the theme; they are never blended, so a verdict
  /// colour is never an in-between shade.
  @override
  SnColors lerp(SnColors? other, double t) =>
      other == null || t < 0.5 ? this : other;
}
