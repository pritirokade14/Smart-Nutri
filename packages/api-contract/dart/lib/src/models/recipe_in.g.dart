// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipe_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipeIn _$RecipeInFromJson(Map<String, dynamic> json) => RecipeIn(
  ingredients: (json['ingredients'] as List<dynamic>)
      .map((e) => RecipeIngredientIn.fromJson(e as Map<String, dynamic>))
      .toList(),
  name: json['name'] as String,
  clientId: json['client_id'] as String?,
  cookedWeightG: json['cooked_weight_g'] as num?,
  servings: json['servings'] as num?,
);

Map<String, dynamic> _$RecipeInToJson(RecipeIn instance) => <String, dynamic>{
  'client_id': instance.clientId,
  'cooked_weight_g': instance.cookedWeightG,
  'ingredients': instance.ingredients,
  'name': instance.name,
  'servings': instance.servings,
};
