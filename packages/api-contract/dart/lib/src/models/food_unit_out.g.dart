// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'food_unit_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FoodUnitOut _$FoodUnitOutFromJson(Map<String, dynamic> json) => FoodUnitOut(
  code: json['code'] as String,
  gramsPerUnit: json['grams_per_unit'] as num,
  kind: FoodUnitOutKind.fromJson(json['kind'] as String),
  ml: json['ml'] as num?,
  source: FoodUnitOutSource.fromJson(json['source'] as String),
  userOverride: json['user_override'] as bool,
);

Map<String, dynamic> _$FoodUnitOutToJson(FoodUnitOut instance) =>
    <String, dynamic>{
      'code': instance.code,
      'grams_per_unit': instance.gramsPerUnit,
      'kind': _$FoodUnitOutKindEnumMap[instance.kind]!,
      'ml': instance.ml,
      'source': _$FoodUnitOutSourceEnumMap[instance.source]!,
      'user_override': instance.userOverride,
    };

const _$FoodUnitOutKindEnumMap = {
  FoodUnitOutKind.mass: 'mass',
  FoodUnitOutKind.volume: 'volume',
  FoodUnitOutKind.count: 'count',
  FoodUnitOutKind.$unknown: r'$unknown',
};

const _$FoodUnitOutSourceEnumMap = {
  FoodUnitOutSource.mass: 'mass',
  FoodUnitOutSource.serving: 'serving',
  FoodUnitOutSource.portionUser: 'portion_user',
  FoodUnitOutSource.portionGlobal: 'portion_global',
  FoodUnitOutSource.density: 'density',
  FoodUnitOutSource.volumeBasis: 'volume_basis',
  FoodUnitOutSource.$unknown: r'$unknown',
};
