// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dish_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DishOut _$DishOutFromJson(Map<String, dynamic> json) => DishOut(
  cookedWeightG: json['cooked_weight_g'] as num?,
  ingredients: (json['ingredients'] as List<dynamic>)
      .map((e) => DishIngredientOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  servings: (json['servings'] as num?)?.toInt(),
);

Map<String, dynamic> _$DishOutToJson(DishOut instance) => <String, dynamic>{
  'cooked_weight_g': instance.cookedWeightG,
  'ingredients': instance.ingredients,
  'servings': instance.servings,
};
