// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'incomplete_nutrients.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

IncompleteNutrients _$IncompleteNutrientsFromJson(Map<String, dynamic> json) =>
    IncompleteNutrients(
      energyKcal: json['energy_kcal'] as bool,
      proteinG: json['protein_g'] as bool,
      saltG: json['salt_g'] as bool,
      sugarsG: json['sugars_g'] as bool,
    );

Map<String, dynamic> _$IncompleteNutrientsToJson(
  IncompleteNutrients instance,
) => <String, dynamic>{
  'energy_kcal': instance.energyKcal,
  'protein_g': instance.proteinG,
  'salt_g': instance.saltG,
  'sugars_g': instance.sugarsG,
};
