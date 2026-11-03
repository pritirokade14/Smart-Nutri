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
  memberStatus: json['member_status'] == null
      ? null
      : MemberStatus.fromJson(json['member_status'] as String),
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  proteinG: json['protein_g'] as num?,
  proteinPer100kcal: json['protein_per_100kcal'] as num?,
  source: SearchHitSource.fromJson(json['source'] as String),
  offDegraded: json['off_degraded'] as bool? ?? false,
);

Map<String, dynamic> _$SearchHitToJson(SearchHit instance) => <String, dynamic>{
  'attribution': instance.attribution,
  'barcode': instance.barcode,
  'brand': instance.brand,
  'grade': _$NutriScoreGradeEnumMap[instance.grade],
  'member_status': _$MemberStatusEnumMap[instance.memberStatus],
  'name': instance.name,
  'off_degraded': instance.offDegraded,
  'product_id': instance.productId,
  'protein_g': instance.proteinG,
  'protein_per_100kcal': instance.proteinPer100kcal,
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

const _$MemberStatusEnumMap = {
  MemberStatus.ok: 'ok',
  MemberStatus.caution: 'caution',
  MemberStatus.unknown: 'unknown',
  MemberStatus.avoid: 'avoid',
  MemberStatus.$unknown: r'$unknown',
};

const _$SearchHitSourceEnumMap = {
  SearchHitSource.ours: 'ours',
  SearchHitSource.off: 'off',
  SearchHitSource.$unknown: r'$unknown',
};
