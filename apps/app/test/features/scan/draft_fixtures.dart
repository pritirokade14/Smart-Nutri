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
  'warnings': <String>[],
  // The server's hints for a clean per-100 g draft (as in
  // packages/test-fixtures/drafts/clean.json). Drafts with save rules come
  // from those shared fixtures, never from here.
  'confirm': <String, Object?>{
    'basis_required': false,
    'category_required': false,
    'columns': <String, Object?>{
      'per_100g': <String, Object?>{
        'printed': true,
        'shared': false,
        'confirm_fields': <String>[],
        'sodium_unit_required': false,
      },
      'per_serving': null,
    },
  },
};

ProductDraft draftFrom(Map<String, Object?> json) =>
    ProductDraft.fromJson(json);

ProductDraft baseDraft() => draftFrom(baseDraftJson());

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
