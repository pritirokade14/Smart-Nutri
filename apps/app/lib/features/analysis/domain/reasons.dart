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
        when p['ingredients'] is List && (p['ingredients']! as List).isEmpty:
      return 'reason_variant.diet_violation_mark_only';
  }
  return 'reason.${reason.code}';
}

/// The reasons to show, in API order (already severity-sorted by the engine;
/// never re-sorted here). The engine emits `nutrient_missing` once per
/// (nutrient, rule); only the first line per nutrient is kept
/// (CROSS-PLAN-NOTES item 13). Nothing else is dropped or merged.
List<ReasonOut> displayReasons(List<ReasonOut> reasons) {
  final seenMissing = <Object?>{};
  return [
    for (final r in reasons)
      if (r.code != 'nutrient_missing' ||
          seenMissing.add(reasonParams(r)['nutrient']))
        r,
  ];
}
