// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'search_hit.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SearchHit _$SearchHitFromJson(Map<String, dynamic> json) => SearchHit(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  brand: json['brand'] as String?,
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  source: SearchHitSource.fromJson(json['source'] as String),
  offDegraded: json['off_degraded'] as bool? ?? false,
);

Map<String, dynamic> _$SearchHitToJson(SearchHit instance) => <String, dynamic>{
  'attribution': instance.attribution,
  'barcode': instance.barcode,
  'brand': instance.brand,
  'grade': _$NutriScoreGradeEnumMap[instance.grade],
  'name': instance.name,
  'off_degraded': instance.offDegraded,
  'product_id': instance.productId,
  'source': _$SearchHitSourceEnumMap[instance.source]!,
};

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$SearchHitSourceEnumMap = {
  SearchHitSource.ours: 'ours',
  SearchHitSource.off: 'off',
  SearchHitSource.$unknown: r'$unknown',
};
