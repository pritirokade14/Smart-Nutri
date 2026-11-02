// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'nutrients_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NutrientsOut _$NutrientsOutFromJson(Map<String, dynamic> json) => NutrientsOut(
  carbsG: json['carbs_g'] as num?,
  energyKcal: json['energy_kcal'] as num?,
  fatG: json['fat_g'] as num?,
  fiberG: json['fiber_g'] as num?,
  proteinG: json['protein_g'] as num?,
  saltG: json['salt_g'] as num?,
  satFatG: json['sat_fat_g'] as num?,
  sodiumMg: json['sodium_mg'] as num?,
  sugarsG: json['sugars_g'] as num?,
);

Map<String, dynamic> _$NutrientsOutToJson(NutrientsOut instance) =>
    <String, dynamic>{
      'carbs_g': instance.carbsG,
      'energy_kcal': instance.energyKcal,
      'fat_g': instance.fatG,
      'fiber_g': instance.fiberG,
      'protein_g': instance.proteinG,
      'salt_g': instance.saltG,
      'sat_fat_g': instance.satFatG,
      'sodium_mg': instance.sodiumMg,
      'sugars_g': instance.sugarsG,
    };
