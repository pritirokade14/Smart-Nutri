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
      : MealOutGrade.fromJson(json['grade'] as String),
  grams: json['grams'] as num,
  id: json['id'] as String,
  memberId: json['member_id'] as String,
  nutrients: NutrientSnapshot.fromJson(
    json['nutrients'] as Map<String, dynamic>,
  ),
  productId: json['product_id'] as String?,
  productName: json['product_name'] as String,
);

Map<String, dynamic> _$MealOutToJson(MealOut instance) => <String, dynamic>{
  'attribution': instance.attribution,
  'barcode': instance.barcode,
  'client_id': instance.clientId,
  'eaten_at': instance.eatenAt.toIso8601String(),
  'grade': _$MealOutGradeEnumMap[instance.grade],
  'grams': instance.grams,
  'id': instance.id,
  'member_id': instance.memberId,
  'nutrients': instance.nutrients,
  'product_id': instance.productId,
  'product_name': instance.productName,
};

const _$MealOutGradeEnumMap = {
  MealOutGrade.a: 'A',
  MealOutGrade.b: 'B',
  MealOutGrade.c: 'C',
  MealOutGrade.d: 'D',
  MealOutGrade.e: 'E',
  MealOutGrade.$unknown: r'$unknown',
};
