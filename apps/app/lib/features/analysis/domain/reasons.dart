// The generated package has no top-level library file, only src/export.dart.
// ignore: implementation_imports
import 'package:smartnutri_api/src/export.dart';

/// The reason's params as a map (empty when the API sent none).
Map<String, Object?> reasonParams(ReasonOut reason) {
  final p = reason.params;
  return p is Map ? p.cast<String, Object?>() : const {};
}

/// The i18n message key for [reason] (`packages/i18n/README.md`, step 1):
/// `reason.<code>`, or a `reason_variant.*` key for the documented cases.
String reasonMessageKey(ReasonOut reason) {
  final p = reasonParams(reason);
  switch (reason.code) {
    case 'nutrient_missing' when p['reason'] == 'low_confidence':
      return 'reason_variant.nutrient_missing_low_confidence';
    case 'diet_violation'
        when p['ingredients'] == null ||
            (p['ingredients'] is List && (p['ingredients']! as List).isEmpty):
      return 'reason_variant.diet_violation_mark_only';
  }
  return 'reason.${reason.code}';
}

/// The reasons to show, in API order (already severity-sorted by the engine;
/// never re-sorted here). The engine emits `nutrient_missing` once per
/// (nutrient, rule); only the first line per (nutrient, message key) is kept
/// so a low-confidence variant and a plain line for the same nutrient both
/// show (CROSS-PLAN-NOTES item 13). Nothing else is dropped or merged.
List<ReasonOut> displayReasons(List<ReasonOut> reasons) {
  final seenMissing = <(Object?, String)>{};
  return [
    for (final r in reasons)
      if (r.code != 'nutrient_missing' ||
          seenMissing.add((reasonParams(r)['nutrient'], reasonMessageKey(r))))
        r,
  ];
}

/// Ruling R22: avoid and unknown reasons (including a severity this build
/// does not recognise) and every allergen reason are always visible.
bool isAlwaysVisible(ReasonOut r) =>
    r.code.startsWith('allergen_') ||
    (r.severity != ReasonOutSeverity.caution &&
        r.severity != ReasonOutSeverity.ok);

/// Splits [reasons] into the always-visible group and the collapsed
/// caution/ok group, each in API order.
({List<ReasonOut> visible, List<ReasonOut> collapsed}) splitReasons(
  List<ReasonOut> reasons,
) => (
  visible: [
    for (final r in reasons)
      if (isAlwaysVisible(r)) r,
  ],
  collapsed: [
    for (final r in reasons)
      if (!isAlwaysVisible(r)) r,
  ],
);
