// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipe_ingredient_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipeIngredientIn _$RecipeIngredientInFromJson(Map<String, dynamic> json) =>
    RecipeIngredientIn(
      quantity: json['quantity'] as num,
      unit: RecipeIngredientInUnit.fromJson(json['unit'] as String),
      barcode: json['barcode'] as String?,
      customFoodId: json['custom_food_id'] as String?,
      foodId: json['food_id'] as String?,
      productId: json['product_id'] as String?,
    );

Map<String, dynamic> _$RecipeIngredientInToJson(RecipeIngredientIn instance) =>
    <String, dynamic>{
      'barcode': instance.barcode,
      'custom_food_id': instance.customFoodId,
      'food_id': instance.foodId,
      'product_id': instance.productId,
      'quantity': instance.quantity,
      'unit': _$RecipeIngredientInUnitEnumMap[instance.unit]!,
    };

const _$RecipeIngredientInUnitEnumMap = {
  RecipeIngredientInUnit.g: 'g',
  RecipeIngredientInUnit.ml: 'ml',
  RecipeIngredientInUnit.serving: 'serving',
  RecipeIngredientInUnit.piece: 'piece',
  RecipeIngredientInUnit.pieceSmall: 'piece_small',
  RecipeIngredientInUnit.pieceMedium: 'piece_medium',
  RecipeIngredientInUnit.pieceLarge: 'piece_large',
  RecipeIngredientInUnit.roti: 'roti',
  RecipeIngredientInUnit.slice: 'slice',
  RecipeIngredientInUnit.katori: 'katori',
  RecipeIngredientInUnit.katoriSmall: 'katori_small',
  RecipeIngredientInUnit.katoriMedium: 'katori_medium',
  RecipeIngredientInUnit.katoriLarge: 'katori_large',
  RecipeIngredientInUnit.cup: 'cup',
  RecipeIngredientInUnit.glass: 'glass',
  RecipeIngredientInUnit.tbsp: 'tbsp',
  RecipeIngredientInUnit.tsp: 'tsp',
  RecipeIngredientInUnit.$unknown: r'$unknown',
};
