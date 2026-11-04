// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'compare_side.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CompareSide _$CompareSideFromJson(Map<String, dynamic> json) => CompareSide(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  brand: json['brand'] as String?,
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  highIn: (json['high_in'] as List<dynamic>).map((e) => e as String).toList(),
  memberStatus: json['member_status'] == null
      ? null
      : MemberStatus.fromJson(json['member_status'] as String),
  name: json['name'] as String,
  per100g: NutrientsOut.fromJson(json['per_100g'] as Map<String, dynamic>),
  productId: json['product_id'] as String?,
  proteinPer100kcal: json['protein_per_100kcal'] as num?,
  proteinPerServingG: json['protein_per_serving_g'] as num?,
  servingSizeG: json['serving_size_g'] as num?,
  sugarsPerServingG: json['sugars_per_serving_g'] as num?,
);

Map<String, dynamic> _$CompareSideToJson(CompareSide instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'barcode': instance.barcode,
      'brand': instance.brand,
      'grade': _$NutriScoreGradeEnumMap[instance.grade],
      'high_in': instance.highIn,
      'member_status': _$MemberStatusEnumMap[instance.memberStatus],
      'name': instance.name,
      'per_100g': instance.per100g,
      'product_id': instance.productId,
      'protein_per_100kcal': instance.proteinPer100kcal,
      'protein_per_serving_g': instance.proteinPerServingG,
      'serving_size_g': instance.servingSizeG,
      'sugars_per_serving_g': instance.sugarsPerServingG,
    };

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$MemberStatusEnumMap = {
  MemberStatus.ok: 'ok',
  MemberStatus.caution: 'caution',
  MemberStatus.unknown: 'unknown',
  MemberStatus.avoid: 'avoid',
  MemberStatus.$unknown: r'$unknown',
};
