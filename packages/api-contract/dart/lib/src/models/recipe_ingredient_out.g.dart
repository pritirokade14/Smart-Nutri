// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipe_ingredient_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipeIngredientOut _$RecipeIngredientOutFromJson(Map<String, dynamic> json) =>
    RecipeIngredientOut(
      attribution: json['attribution'] as String?,
      available: json['available'] as bool,
      barcode: json['barcode'] as String?,
      customFoodId: json['custom_food_id'] as String?,
      foodId: json['food_id'] as String?,
      grams: json['grams'] as num,
      name: json['name'] as String,
      position: (json['position'] as num).toInt(),
      productId: json['product_id'] as String?,
      quantity: json['quantity'] as num,
      sourceKind: RecipeIngredientOutSourceKind.fromJson(
        json['source_kind'] as String,
      ),
      unit: json['unit'] as String,
    );

Map<String, dynamic> _$RecipeIngredientOutToJson(
  RecipeIngredientOut instance,
) => <String, dynamic>{
  'attribution': instance.attribution,
  'available': instance.available,
  'barcode': instance.barcode,
  'custom_food_id': instance.customFoodId,
  'food_id': instance.foodId,
  'grams': instance.grams,
  'name': instance.name,
  'position': instance.position,
  'product_id': instance.productId,
  'quantity': instance.quantity,
  'source_kind': _$RecipeIngredientOutSourceKindEnumMap[instance.sourceKind]!,
  'unit': instance.unit,
};

const _$RecipeIngredientOutSourceKindEnumMap = {
  RecipeIngredientOutSourceKind.product: 'product',
  RecipeIngredientOutSourceKind.off: 'off',
  RecipeIngredientOutSourceKind.food: 'food',
  RecipeIngredientOutSourceKind.customFood: 'custom_food',
  RecipeIngredientOutSourceKind.$unknown: r'$unknown',
};
