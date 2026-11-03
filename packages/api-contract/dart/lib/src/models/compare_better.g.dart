// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'compare_better.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CompareBetter _$CompareBetterFromJson(Map<String, dynamic> json) =>
    CompareBetter(
      energyKcal: BetterSide.fromJson(json['energy_kcal'] as String),
      fiberG: BetterSide.fromJson(json['fiber_g'] as String),
      grade: BetterSide.fromJson(json['grade'] as String),
      proteinG: BetterSide.fromJson(json['protein_g'] as String),
      saltG: BetterSide.fromJson(json['salt_g'] as String),
      satFatG: BetterSide.fromJson(json['sat_fat_g'] as String),
      sugarsG: BetterSide.fromJson(json['sugars_g'] as String),
    );

Map<String, dynamic> _$CompareBetterToJson(CompareBetter instance) =>
    <String, dynamic>{
      'energy_kcal': _$BetterSideEnumMap[instance.energyKcal]!,
      'fiber_g': _$BetterSideEnumMap[instance.fiberG]!,
      'grade': _$BetterSideEnumMap[instance.grade]!,
      'protein_g': _$BetterSideEnumMap[instance.proteinG]!,
      'salt_g': _$BetterSideEnumMap[instance.saltG]!,
      'sat_fat_g': _$BetterSideEnumMap[instance.satFatG]!,
      'sugars_g': _$BetterSideEnumMap[instance.sugarsG]!,
    };

const _$BetterSideEnumMap = {
  BetterSide.a: 'a',
  BetterSide.b: 'b',
  BetterSide.same: 'same',
  BetterSide.unknown: 'unknown',
  BetterSide.$unknown: r'$unknown',
};
