import 'package:smartnutri_api/src/export.dart';

/// One printed nutrition column in draft units; every field present (null =
/// not printed).
Map<String, Object?> column({
  num? energyKcal,
  num? proteinG,
  num? carbsG,
  num? sugarsG,
  num? addedSugarsG,
  num? fatG,
  num? satFatG,
  num? transFatG,
  num? fiberG,
  num? saltG,
  num? sodiumMg,
}) => {
  'energy_kcal': energyKcal,
  'protein_g': proteinG,
  'carbs_g': carbsG,
  'sugars_g': sugarsG,
  'added_sugars_g': addedSugarsG,
  'fat_g': fatG,
  'sat_fat_g': satFatG,
  'trans_fat_g': transFatG,
  'fiber_g': fiberG,
  'salt_g': saltG,
  'sodium_mg': sodiumMg,
};

/// A clean per-100 g biscuit label: no warnings, fibre not printed.
Map<String, Object?> baseDraftJson() => {
  'name': 'Marie Biscuit',
  'brand': 'Acme',
  'category': 'general',
  'per_100g': column(
    energyKcal: 451.37,
    proteinG: 7.5,
    carbsG: 74.2,
    sugarsG: 21.3,
    fatG: 13.4,
    satFatG: 6.2,
    saltG: 0.9,
    sodiumMg: 360,
  ),
  'per_serving': null,
  'serving_size_g': null,
  'ingredients': ['Wheat flour', 'Sugar', 'Palm oil'],
  'allergen_statement': 'Contains wheat (gluten).',
  'may_contain_statement': 'May contain milk.',
  'claims': <String>[],
  'veg_mark': 'veg',
  'confidence': 0.92,
  'derived_from_serving': false,
  'engine_withheld': <String>[],
  'positive_suppressed': <String>[],
  'warnings': <String>[],
};

ProductDraft draftFrom(Map<String, Object?> json) =>
    ProductDraft.fromJson(json);

ProductDraft baseDraft() => draftFrom(baseDraftJson());

/// `implausible_value:sugars_g` (sugars above carbs).
ProductDraft implausibleDraft() {
  final j = baseDraftJson();
  (j['per_100g']! as Map<String, Object?>)['sugars_g'] = 95;
  j['warnings'] = ['implausible_value:sugars_g'];
  return draftFrom(j);
}

/// A per-serving-only label without a serving size: nothing per 100 g.
ProductDraft per100gMissingDraft() {
  final j = baseDraftJson();
  j['per_100g'] = column();
  j['per_serving'] = column(energyKcal: 120, proteinG: 2, sugarsG: 6);
  j['warnings'] = ['per_100g_missing', 'per_serving_ignored'];
  return draftFrom(j);
}

/// An upper-bound ("<0.5 g") protein the engine holds back.
ProductDraft withheldProteinDraft() {
  final j = baseDraftJson();
  (j['per_100g']! as Map<String, Object?>)['protein_g'] = 0.5;
  j['engine_withheld'] = ['protein_g'];
  j['positive_suppressed'] = ['protein_g'];
  j['warnings'] = ['upper_bound:per_100g.protein_g'];
  return draftFrom(j);
}

/// Values printed in the per-100 g column, but the label says "per serving".
ProductDraft basisMismatchDraft() {
  final j = baseDraftJson();
  j['engine_withheld'] = [
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
  j['warnings'] = ['basis_mismatch'];
  return draftFrom(j);
}

/// Sodium printed as "0.4" with no unit on the per-100 g column.
ProductDraft sodiumUnitDraft() {
  final j = baseDraftJson();
  (j['per_100g']! as Map<String, Object?>)['sodium_mg'] = 0.4;
  j['engine_withheld'] = ['sodium_mg'];
  j['warnings'] = ['unit_unconfirmed:per_100g.sodium_mg'];
  return draftFrom(j);
}

/// Only a per-serving column (30 g serving) was printed; the server derived
/// per-100 g values from it.
Map<String, Object?> derivedDraftJson() {
  final j = baseDraftJson();
  j['per_100g'] = column(
    energyKcal: 400,
    proteinG: 6.666666666666667,
    carbsG: 70,
    sugarsG: 20,
    fatG: 13.333333333333334,
    satFatG: 6.666666666666667,
    saltG: 1,
    sodiumMg: 400,
  );
  j['per_serving'] = column(
    energyKcal: 120,
    proteinG: 2,
    carbsG: 21,
    sugarsG: 6,
    fatG: 4,
    satFatG: 2,
    saltG: 0.3,
    sodiumMg: 120,
  );
  j['serving_size_g'] = 30;
  j['derived_from_serving'] = true;
  j['warnings'] = ['derived_from_serving'];
  return j;
}

ProductDraft derivedDraft() => draftFrom(derivedDraftJson());

/// The model guessed the category from weak evidence.
ProductDraft categoryCheckDraft() {
  final j = baseDraftJson();
  j['category'] = 'beverage';
  j['warnings'] = ['category_check'];
  return draftFrom(j);
}

ProductDraft lowConfidenceDraft() {
  final j = baseDraftJson();
  j['confidence'] = 0.55;
  j['warnings'] = ['low_confidence', 'unreadable_field:per_100g.fiber_g'];
  return draftFrom(j);
}

ScanDraftOut scanOut(ProductDraft draft, {String scanId = 'scan-1'}) =>
    ScanDraftOut(
      cached: false,
      draft: draft,
      promptVersion: 'label-v1',
      scanId: scanId,
    );
