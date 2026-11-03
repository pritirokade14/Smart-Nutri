// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'nutrient_bands.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NutrientBands _$NutrientBandsFromJson(Map<String, dynamic> json) =>
    NutrientBands(
      kcal: NutrientBand.fromJson(json['kcal'] as String),
      proteinG: NutrientBand.fromJson(json['protein_g'] as String),
      saltG: NutrientBand.fromJson(json['salt_g'] as String),
      sugarG: NutrientBand.fromJson(json['sugar_g'] as String),
    );

Map<String, dynamic> _$NutrientBandsToJson(NutrientBands instance) =>
    <String, dynamic>{
      'kcal': _$NutrientBandEnumMap[instance.kcal]!,
      'protein_g': _$NutrientBandEnumMap[instance.proteinG]!,
      'salt_g': _$NutrientBandEnumMap[instance.saltG]!,
      'sugar_g': _$NutrientBandEnumMap[instance.sugarG]!,
    };

const _$NutrientBandEnumMap = {
  NutrientBand.ok: 'ok',
  NutrientBand.near: 'near',
  NutrientBand.over: 'over',
  NutrientBand.unknown: 'unknown',
  NutrientBand.$unknown: r'$unknown',
};
