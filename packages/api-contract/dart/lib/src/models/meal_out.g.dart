// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealOut _$MealOutFromJson(Map<String, dynamic> json) => MealOut(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  clientId: json['client_id'] as String?,
  eatenAt: DateTime.parse(json['eaten_at'] as String),
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  grams: json['grams'] as num?,
  id: json['id'] as String,
  incomplete: (json['incomplete'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  localDate: DateTime.parse(json['local_date'] as String),
  mealSlotId: json['meal_slot_id'] as String,
  memberId: json['member_id'] as String,
  nutrients: NutrientSnapshot.fromJson(
    json['nutrients'] as Map<String, dynamic>,
  ),
  productId: json['product_id'] as String?,
  productName: json['product_name'] as String,
  sourceKind: MealOutSourceKind.fromJson(json['source_kind'] as String),
  updatedAt: DateTime.parse(json['updated_at'] as String),
);

Map<String, dynamic> _$MealOutToJson(MealOut instance) => <String, dynamic>{
  'attribution': instance.attribution,
  'barcode': instance.barcode,
  'client_id': instance.clientId,
  'eaten_at': instance.eatenAt.toIso8601String(),
  'grade': _$NutriScoreGradeEnumMap[instance.grade],
  'grams': instance.grams,
  'id': instance.id,
  'incomplete': instance.incomplete,
  'local_date': instance.localDate.toIso8601String(),
  'meal_slot_id': instance.mealSlotId,
  'member_id': instance.memberId,
  'nutrients': instance.nutrients,
  'product_id': instance.productId,
  'product_name': instance.productName,
  'source_kind': _$MealOutSourceKindEnumMap[instance.sourceKind]!,
  'updated_at': instance.updatedAt.toIso8601String(),
};

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$MealOutSourceKindEnumMap = {
  MealOutSourceKind.product: 'product',
  MealOutSourceKind.off: 'off',
  MealOutSourceKind.quickAdd: 'quick_add',
  MealOutSourceKind.$unknown: r'$unknown',
};
