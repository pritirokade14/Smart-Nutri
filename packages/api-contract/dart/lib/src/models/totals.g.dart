// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'totals.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Totals _$TotalsFromJson(Map<String, dynamic> json) => Totals(
  energyKcal: json['energy_kcal'] as num?,
  proteinG: json['protein_g'] as num?,
  saltG: json['salt_g'] as num?,
  sugarsG: json['sugars_g'] as num?,
);

Map<String, dynamic> _$TotalsToJson(Totals instance) => <String, dynamic>{
  'energy_kcal': instance.energyKcal,
  'protein_g': instance.proteinG,
  'salt_g': instance.saltG,
  'sugars_g': instance.sugarsG,
};
