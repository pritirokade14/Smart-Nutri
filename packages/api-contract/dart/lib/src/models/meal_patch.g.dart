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
  quick: json['quick'] == null
      ? null
      : QuickIn.fromJson(json['quick'] as Map<String, dynamic>),
  servings: json['servings'] as num?,
);

Map<String, dynamic> _$MealPatchToJson(MealPatch instance) => <String, dynamic>{
  'eaten_at': instance.eatenAt?.toIso8601String(),
  'grams': instance.grams,
  'meal_slot_id': instance.mealSlotId,
  'quick': instance.quick,
  'servings': instance.servings,
};
