// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'product_draft.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProductDraft _$ProductDraftFromJson(Map<String, dynamic> json) => ProductDraft(
  allergenStatement: json['allergen_statement'] as String?,
  brand: json['brand'] as String?,
  category: ProductDraftCategory.fromJson(json['category'] as String),
  claims: (json['claims'] as List<dynamic>).map((e) => e as String).toList(),
  confidence: json['confidence'] as num,
  derivedFromServing: json['derived_from_serving'] as bool,
  engineWithheld: (json['engine_withheld'] as List<dynamic>)
      .map((e) => ProductDraftEngineWithheld.fromJson(e as String))
      .toList(),
  ingredients: (json['ingredients'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  mayContainStatement: json['may_contain_statement'] as String?,
  name: json['name'] as String?,
  per100g: DraftNutrients.fromJson(json['per_100g'] as Map<String, dynamic>),
  perServing: json['per_serving'] == null
      ? null
      : DraftNutrients.fromJson(json['per_serving'] as Map<String, dynamic>),
  positiveSuppressed: (json['positive_suppressed'] as List<dynamic>)
      .map((e) => ProductDraftPositiveSuppressed.fromJson(e as String))
      .toList(),
  servingSizeG: json['serving_size_g'] as num?,
  vegMark: json['veg_mark'] == null
      ? null
      : ProductDraftVegMark.fromJson(json['veg_mark'] as String),
  warnings: (json['warnings'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$ProductDraftToJson(ProductDraft instance) =>
    <String, dynamic>{
      'allergen_statement': instance.allergenStatement,
      'brand': instance.brand,
      'category': _$ProductDraftCategoryEnumMap[instance.category]!,
      'claims': instance.claims,
      'confidence': instance.confidence,
      'derived_from_serving': instance.derivedFromServing,
      'engine_withheld': instance.engineWithheld
          .map((e) => _$ProductDraftEngineWithheldEnumMap[e]!)
          .toList(),
      'ingredients': instance.ingredients,
      'may_contain_statement': instance.mayContainStatement,
      'name': instance.name,
      'per_100g': instance.per100g,
      'per_serving': instance.perServing,
      'positive_suppressed': instance.positiveSuppressed
          .map((e) => _$ProductDraftPositiveSuppressedEnumMap[e]!)
          .toList(),
      'serving_size_g': instance.servingSizeG,
      'veg_mark': _$ProductDraftVegMarkEnumMap[instance.vegMark],
      'warnings': instance.warnings,
    };

const _$ProductDraftCategoryEnumMap = {
  ProductDraftCategory.general: 'general',
  ProductDraftCategory.beverage: 'beverage',
  ProductDraftCategory.water: 'water',
  ProductDraftCategory.cheese: 'cheese',
  ProductDraftCategory.fat: 'fat',
  ProductDraftCategory.$unknown: r'$unknown',
};

const _$ProductDraftEngineWithheldEnumMap = {
  ProductDraftEngineWithheld.energyKcal: 'energy_kcal',
  ProductDraftEngineWithheld.proteinG: 'protein_g',
  ProductDraftEngineWithheld.carbsG: 'carbs_g',
  ProductDraftEngineWithheld.sugarsG: 'sugars_g',
  ProductDraftEngineWithheld.fatG: 'fat_g',
  ProductDraftEngineWithheld.satFatG: 'sat_fat_g',
  ProductDraftEngineWithheld.fiberG: 'fiber_g',
  ProductDraftEngineWithheld.saltG: 'salt_g',
  ProductDraftEngineWithheld.sodiumMg: 'sodium_mg',
  ProductDraftEngineWithheld.$unknown: r'$unknown',
};

const _$ProductDraftPositiveSuppressedEnumMap = {
  ProductDraftPositiveSuppressed.proteinG: 'protein_g',
  ProductDraftPositiveSuppressed.fiberG: 'fiber_g',
  ProductDraftPositiveSuppressed.$unknown: r'$unknown',
};

const _$ProductDraftVegMarkEnumMap = {
  ProductDraftVegMark.veg: 'veg',
  ProductDraftVegMark.nonVeg: 'non_veg',
  ProductDraftVegMark.$unknown: r'$unknown',
};
