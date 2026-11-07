// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'quick_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

QuickIn _$QuickInFromJson(Map<String, dynamic> json) => QuickIn(
  carbsG: json['carbs_g'] as num?,
  energyKcal: json['energy_kcal'] as num?,
  fatG: json['fat_g'] as num?,
  fibreG: json['fibre_g'] as num?,
  name: json['name'] as String?,
  proteinG: json['protein_g'] as num?,
);

Map<String, dynamic> _$QuickInToJson(QuickIn instance) => <String, dynamic>{
  'carbs_g': instance.carbsG,
  'energy_kcal': instance.energyKcal,
  'fat_g': instance.fatG,
  'fibre_g': instance.fibreG,
  'name': instance.name,
  'protein_g': instance.proteinG,
};
