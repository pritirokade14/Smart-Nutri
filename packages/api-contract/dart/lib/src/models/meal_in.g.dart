// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealIn _$MealInFromJson(Map<String, dynamic> json) => MealIn(
  memberId: json['member_id'] as String,
  barcode: json['barcode'] as String?,
  clientId: json['client_id'] as String?,
  eatenAt: json['eaten_at'] == null
      ? null
      : DateTime.parse(json['eaten_at'] as String),
  grams: json['grams'] as num?,
  productId: json['product_id'] as String?,
  servings: json['servings'] as num?,
);

Map<String, dynamic> _$MealInToJson(MealIn instance) => <String, dynamic>{
  'barcode': instance.barcode,
  'client_id': instance.clientId,
  'eaten_at': instance.eatenAt?.toIso8601String(),
  'grams': instance.grams,
  'member_id': instance.memberId,
  'product_id': instance.productId,
  'servings': instance.servings,
};
