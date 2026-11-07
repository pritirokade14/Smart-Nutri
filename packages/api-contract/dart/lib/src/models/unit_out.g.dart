// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'unit_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UnitOut _$UnitOutFromJson(Map<String, dynamic> json) => UnitOut(
  code: json['code'] as String,
  grams: json['grams'] as num?,
  kind: UnitOutKind.fromJson(json['kind'] as String),
  ml: json['ml'] as num?,
);

Map<String, dynamic> _$UnitOutToJson(UnitOut instance) => <String, dynamic>{
  'code': instance.code,
  'grams': instance.grams,
  'kind': _$UnitOutKindEnumMap[instance.kind]!,
  'ml': instance.ml,
};

const _$UnitOutKindEnumMap = {
  UnitOutKind.mass: 'mass',
  UnitOutKind.volume: 'volume',
  UnitOutKind.count: 'count',
  UnitOutKind.$unknown: r'$unknown',
};
