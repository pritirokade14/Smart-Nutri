// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipe_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipeOut _$RecipeOutFromJson(Map<String, dynamic> json) => RecipeOut(
  attributions: (json['attributions'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  basisWeightG: json['basis_weight_g'] as num,
  cookedWeightG: json['cooked_weight_g'] as num?,
  id: json['id'] as String,
  incompleteNutrients: (json['incomplete_nutrients'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  ingredients: (json['ingredients'] as List<dynamic>)
      .map((e) => RecipeIngredientOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  name: json['name'] as String,
  numbersHidden: NumbersHidden.fromJson(
    json['numbers_hidden'] as Map<String, dynamic>,
  ),
  per100g: NutrientSnapshot.fromJson(json['per_100g'] as Map<String, dynamic>),
  perServing: json['per_serving'] == null
      ? null
      : NutrientSnapshot.fromJson(json['per_serving'] as Map<String, dynamic>),
  servings: json['servings'] as num?,
  totalRawG: json['total_raw_g'] as num?,
  updatedAt: DateTime.parse(json['updated_at'] as String),
);

Map<String, dynamic> _$RecipeOutToJson(RecipeOut instance) => <String, dynamic>{
  'attributions': instance.attributions,
  'basis_weight_g': instance.basisWeightG,
  'cooked_weight_g': instance.cookedWeightG,
  'id': instance.id,
  'incomplete_nutrients': instance.incompleteNutrients,
  'ingredients': instance.ingredients,
  'name': instance.name,
  'numbers_hidden': instance.numbersHidden,
  'per_100g': instance.per100g,
  'per_serving': instance.perServing,
  'servings': instance.servings,
  'total_raw_g': instance.totalRawG,
  'updated_at': instance.updatedAt.toIso8601String(),
};
