// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'incomplete_nutrients.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

IncompleteNutrients _$IncompleteNutrientsFromJson(Map<String, dynamic> json) =>
    IncompleteNutrients(
      carbsG: json['carbs_g'] as bool,
      energyKcal: json['energy_kcal'] as bool,
      fatG: json['fat_g'] as bool,
      fibreG: json['fibre_g'] as bool,
      proteinG: json['protein_g'] as bool,
      saltG: json['salt_g'] as bool,
      sugarsG: json['sugars_g'] as bool,
    );

Map<String, dynamic> _$IncompleteNutrientsToJson(
  IncompleteNutrients instance,
) => <String, dynamic>{
  'carbs_g': instance.carbsG,
  'energy_kcal': instance.energyKcal,
  'fat_g': instance.fatG,
  'fibre_g': instance.fibreG,
  'protein_g': instance.proteinG,
  'salt_g': instance.saltG,
  'sugars_g': instance.sugarsG,
};
