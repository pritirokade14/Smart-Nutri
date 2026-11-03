// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alternative_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AlternativeOut _$AlternativeOutFromJson(
  Map<String, dynamic> json,
) => AlternativeOut(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  brand: json['brand'] as String?,
  grade: AlternativeOutGrade.fromJson(json['grade'] as String),
  highIn: (json['high_in'] as List<dynamic>).map((e) => e as String).toList(),
  imageUrl: json['image_url'] as String?,
  memberStatus: json['member_status'] == null
      ? null
      : AlternativeOutMemberStatus.fromJson(json['member_status'] as String),
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  sugarsG: json['sugars_g'] as num?,
);

Map<String, dynamic> _$AlternativeOutToJson(
  AlternativeOut instance,
) => <String, dynamic>{
  'attribution': instance.attribution,
  'barcode': instance.barcode,
  'brand': instance.brand,
  'grade': _$AlternativeOutGradeEnumMap[instance.grade]!,
  'high_in': instance.highIn,
  'image_url': instance.imageUrl,
  'member_status': _$AlternativeOutMemberStatusEnumMap[instance.memberStatus],
  'name': instance.name,
  'product_id': instance.productId,
  'sugars_g': instance.sugarsG,
};

const _$AlternativeOutGradeEnumMap = {
  AlternativeOutGrade.a: 'A',
  AlternativeOutGrade.b: 'B',
  AlternativeOutGrade.c: 'C',
  AlternativeOutGrade.d: 'D',
  AlternativeOutGrade.e: 'E',
  AlternativeOutGrade.$unknown: r'$unknown',
};

const _$AlternativeOutMemberStatusEnumMap = {
  AlternativeOutMemberStatus.ok: 'ok',
  AlternativeOutMemberStatus.caution: 'caution',
  AlternativeOutMemberStatus.unknown: 'unknown',
  AlternativeOutMemberStatus.avoid: 'avoid',
  AlternativeOutMemberStatus.$unknown: r'$unknown',
};
