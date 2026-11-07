// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'nutrient_snapshot.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NutrientSnapshot _$NutrientSnapshotFromJson(Map<String, dynamic> json) =>
    NutrientSnapshot(
      carbsG: json['carbs_g'] as num?,
      energyKcal: json['energy_kcal'] as num?,
      fatG: json['fat_g'] as num?,
      fibreG: json['fibre_g'] as num?,
      proteinG: json['protein_g'] as num?,
      saltG: json['salt_g'] as num?,
      satFatG: json['sat_fat_g'] as num?,
      sugarsG: json['sugars_g'] as num?,
    );

Map<String, dynamic> _$NutrientSnapshotToJson(NutrientSnapshot instance) =>
    <String, dynamic>{
      'carbs_g': instance.carbsG,
      'energy_kcal': instance.energyKcal,
      'fat_g': instance.fatG,
      'fibre_g': instance.fibreG,
      'protein_g': instance.proteinG,
      'salt_g': instance.saltG,
      'sat_fat_g': instance.satFatG,
      'sugars_g': instance.sugarsG,
    };
