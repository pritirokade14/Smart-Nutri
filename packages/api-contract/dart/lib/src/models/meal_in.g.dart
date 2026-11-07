// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealIn _$MealInFromJson(Map<String, dynamic> json) => MealIn(
  barcode: json['barcode'] as String?,
  clientId: json['client_id'] as String?,
  eatenAt: json['eaten_at'] == null
      ? null
      : DateTime.parse(json['eaten_at'] as String),
  grams: json['grams'] as num?,
  localDate: json['local_date'] == null
      ? null
      : DateTime.parse(json['local_date'] as String),
  mealSlotId: json['meal_slot_id'] as String?,
  memberId: json['member_id'] as String?,
  productId: json['product_id'] as String?,
  quick: json['quick'] == null
      ? null
      : QuickIn.fromJson(json['quick'] as Map<String, dynamic>),
  servings: json['servings'] as num?,
);

Map<String, dynamic> _$MealInToJson(MealIn instance) => <String, dynamic>{
  'barcode': instance.barcode,
  'client_id': instance.clientId,
  'eaten_at': instance.eatenAt?.toIso8601String(),
  'grams': instance.grams,
  'local_date': instance.localDate?.toIso8601String(),
  'meal_slot_id': instance.mealSlotId,
  'member_id': instance.memberId,
  'product_id': instance.productId,
  'quick': instance.quick,
  'servings': instance.servings,
};
