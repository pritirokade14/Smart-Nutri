// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_patch.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealPatch _$MealPatchFromJson(Map<String, dynamic> json) => MealPatch(
  eatenAt: json['eaten_at'] == null
      ? null
      : DateTime.parse(json['eaten_at'] as String),
  grams: json['grams'] as num?,
  mealSlotId: json['meal_slot_id'] as String?,
  quantity: json['quantity'] as num?,
  quick: json['quick'] == null
      ? null
      : QuickIn.fromJson(json['quick'] as Map<String, dynamic>),
  servings: json['servings'] as num?,
  unit: json['unit'] == null
      ? null
      : MealPatchUnit.fromJson(json['unit'] as String),
);

Map<String, dynamic> _$MealPatchToJson(MealPatch instance) => <String, dynamic>{
  'eaten_at': instance.eatenAt?.toIso8601String(),
  'grams': instance.grams,
  'meal_slot_id': instance.mealSlotId,
  'quantity': instance.quantity,
  'quick': instance.quick,
  'servings': instance.servings,
  'unit': _$MealPatchUnitEnumMap[instance.unit],
};

const _$MealPatchUnitEnumMap = {
  MealPatchUnit.g: 'g',
  MealPatchUnit.ml: 'ml',
  MealPatchUnit.serving: 'serving',
  MealPatchUnit.piece: 'piece',
  MealPatchUnit.pieceSmall: 'piece_small',
  MealPatchUnit.pieceMedium: 'piece_medium',
  MealPatchUnit.pieceLarge: 'piece_large',
  MealPatchUnit.roti: 'roti',
  MealPatchUnit.slice: 'slice',
  MealPatchUnit.katori: 'katori',
  MealPatchUnit.katoriSmall: 'katori_small',
  MealPatchUnit.katoriMedium: 'katori_medium',
  MealPatchUnit.katoriLarge: 'katori_large',
  MealPatchUnit.cup: 'cup',
  MealPatchUnit.glass: 'glass',
  MealPatchUnit.tbsp: 'tbsp',
  MealPatchUnit.tsp: 'tsp',
  MealPatchUnit.$unknown: r'$unknown',
};
