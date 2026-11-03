/// Read-only helpers for `ProductDraft.warnings`. Nothing here changes a value
/// or decides a verdict; it only says what the confirm screen must show.
library;

/// The nine rules-engine nutrient fields, in the API's order.
const engineFields = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'sugars_g',
  'fat_g',
  'sat_fat_g',
  'fiber_g',
  'salt_g',
  'sodium_mg',
];

/// Every nutrient the confirm screen shows, in display order. Added sugars and
/// trans fat are shown and sent, but are not engine inputs.
const formNutrientFields = [
  'energy_kcal',
  'protein_g',
  'carbs_g',
  'sugars_g',
  'added_sugars_g',
  'fat_g',
  'sat_fat_g',
  'trans_fat_g',
  'fiber_g',
  'salt_g',
  'sodium_mg',
];

/// One `warnings[]` entry: `code` or `code:path`, where path is `field` or
/// `column.field` (e.g. `upper_bound:per_100g.protein_g`).
class DraftWarning {
  const DraftWarning(this.code, this.path);

  factory DraftWarning.parse(String raw) {
    final i = raw.indexOf(':');
    return i < 0
        ? DraftWarning(raw, null)
        : DraftWarning(raw.substring(0, i), raw.substring(i + 1));
  }

  final String code;
  final String? path;

  /// The field named by the path (its last segment), if any.
  String? get field {
    final p = path;
    if (p == null || p.isEmpty) return null;
    return p.split('.').last;
  }

  /// The printed column named by the path (`per_100g` / `per_serving`), if any.
  String? get column {
    final p = path;
    if (p == null || !p.contains('.')) return null;
    return p.substring(0, p.indexOf('.'));
  }
}

/// Warning codes whose field is highlighted on the confirm screen.
const highlightingCodes = {
  'implausible_value',
  'unreadable_field',
  'upper_bound',
  'unit_unconfirmed',
};

/// The draft fields to highlight, from the draft's own warnings.
Set<String> highlightedFields(Iterable<DraftWarning> warnings) => {
  for (final w in warnings)
    if (highlightingCodes.contains(w.code)) ?w.field,
};
