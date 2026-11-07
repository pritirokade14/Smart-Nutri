// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recent_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecentItem _$RecentItemFromJson(Map<String, dynamic> json) => RecentItem(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  grams: json['grams'] as num,
  lastEatenAt: DateTime.parse(json['last_eaten_at'] as String),
  mealSlotId: json['meal_slot_id'] as String,
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  sourceKind: RecentItemSourceKind.fromJson(json['source_kind'] as String),
  attributions: (json['attributions'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  foodId: json['food_id'] as String?,
  quantity: json['quantity'] as num?,
  unit: json['unit'] as String?,
);

Map<String, dynamic> _$RecentItemToJson(RecentItem instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'attributions': instance.attributions,
      'barcode': instance.barcode,
      'food_id': instance.foodId,
      'grade': _$NutriScoreGradeEnumMap[instance.grade],
      'grams': instance.grams,
      'last_eaten_at': instance.lastEatenAt.toIso8601String(),
      'meal_slot_id': instance.mealSlotId,
      'name': instance.name,
      'product_id': instance.productId,
      'quantity': instance.quantity,
      'source_kind': _$RecentItemSourceKindEnumMap[instance.sourceKind]!,
      'unit': instance.unit,
    };

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$RecentItemSourceKindEnumMap = {
  RecentItemSourceKind.product: 'product',
  RecentItemSourceKind.off: 'off',
  RecentItemSourceKind.food: 'food',
  RecentItemSourceKind.$unknown: r'$unknown',
};
