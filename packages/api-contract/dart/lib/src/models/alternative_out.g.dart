// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alternative_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AlternativeOut _$AlternativeOutFromJson(Map<String, dynamic> json) =>
    AlternativeOut(
      attribution: json['attribution'] as String?,
      barcode: json['barcode'] as String?,
      brand: json['brand'] as String?,
      grade: NutriScoreGrade.fromJson(json['grade'] as String),
      highIn: (json['high_in'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      imageUrl: json['image_url'] as String?,
      memberStatus: json['member_status'] == null
          ? null
          : MemberStatus.fromJson(json['member_status'] as String),
      name: json['name'] as String,
      productId: json['product_id'] as String?,
      proteinG: json['protein_g'] as num?,
      proteinPer100kcal: json['protein_per_100kcal'] as num?,
      sugarsG: json['sugars_g'] as num?,
    );

Map<String, dynamic> _$AlternativeOutToJson(AlternativeOut instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'barcode': instance.barcode,
      'brand': instance.brand,
      'grade': _$NutriScoreGradeEnumMap[instance.grade]!,
      'high_in': instance.highIn,
      'image_url': instance.imageUrl,
      'member_status': _$MemberStatusEnumMap[instance.memberStatus],
      'name': instance.name,
      'product_id': instance.productId,
      'protein_g': instance.proteinG,
      'protein_per_100kcal': instance.proteinPer100kcal,
      'sugars_g': instance.sugarsG,
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
