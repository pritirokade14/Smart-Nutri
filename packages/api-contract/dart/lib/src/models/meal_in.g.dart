// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealIn _$MealInFromJson(Map<String, dynamic> json) => MealIn(
  barcode: json['barcode'] as String?,
  clientId: json['client_id'] as String?,
  customFoodId: json['custom_food_id'] as String?,
  eatenAt: json['eaten_at'] == null
      ? null
      : DateTime.parse(json['eaten_at'] as String),
  foodId: json['food_id'] as String?,
  grams: json['grams'] as num?,
  localDate: json['local_date'] == null
      ? null
      : DateTime.parse(json['local_date'] as String),
  mealSlotId: json['meal_slot_id'] as String?,
  memberId: json['member_id'] as String?,
  productId: json['product_id'] as String?,
  quantity: json['quantity'] as num?,
  quick: json['quick'] == null
      ? null
      : QuickIn.fromJson(json['quick'] as Map<String, dynamic>),
  recipeId: json['recipe_id'] as String?,
  servings: json['servings'] as num?,
  unit: json['unit'] == null
      ? null
      : MealInUnit.fromJson(json['unit'] as String),
);

Map<String, dynamic> _$MealInToJson(MealIn instance) => <String, dynamic>{
  'barcode': instance.barcode,
  'client_id': instance.clientId,
  'custom_food_id': instance.customFoodId,
  'eaten_at': instance.eatenAt?.toIso8601String(),
  'food_id': instance.foodId,
  'grams': instance.grams,
  'local_date': instance.localDate?.toIso8601String(),
  'meal_slot_id': instance.mealSlotId,
  'member_id': instance.memberId,
  'product_id': instance.productId,
  'quantity': instance.quantity,
  'quick': instance.quick,
  'recipe_id': instance.recipeId,
  'servings': instance.servings,
  'unit': _$MealInUnitEnumMap[instance.unit],
};

const _$MealInUnitEnumMap = {
  MealInUnit.g: 'g',
  MealInUnit.ml: 'ml',
  MealInUnit.serving: 'serving',
  MealInUnit.piece: 'piece',
  MealInUnit.pieceSmall: 'piece_small',
  MealInUnit.pieceMedium: 'piece_medium',
  MealInUnit.pieceLarge: 'piece_large',
  MealInUnit.roti: 'roti',
  MealInUnit.slice: 'slice',
  MealInUnit.katori: 'katori',
  MealInUnit.katoriSmall: 'katori_small',
  MealInUnit.katoriMedium: 'katori_medium',
  MealInUnit.katoriLarge: 'katori_large',
  MealInUnit.cup: 'cup',
  MealInUnit.glass: 'glass',
  MealInUnit.tbsp: 'tbsp',
  MealInUnit.tsp: 'tsp',
  MealInUnit.$unknown: r'$unknown',
};
