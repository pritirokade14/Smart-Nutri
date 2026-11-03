// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'column_confirm.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ColumnConfirm _$ColumnConfirmFromJson(Map<String, dynamic> json) =>
    ColumnConfirm(
      confirmFields: (json['confirm_fields'] as List<dynamic>)
          .map((e) => ColumnConfirmConfirmFields.fromJson(e as String))
          .toList(),
      printed: json['printed'] as bool,
      shared: json['shared'] as bool,
      sodiumUnitRequired: json['sodium_unit_required'] as bool,
    );

Map<String, dynamic> _$ColumnConfirmToJson(ColumnConfirm instance) =>
    <String, dynamic>{
      'confirm_fields': instance.confirmFields
          .map((e) => _$ColumnConfirmConfirmFieldsEnumMap[e]!)
          .toList(),
      'printed': instance.printed,
      'shared': instance.shared,
      'sodium_unit_required': instance.sodiumUnitRequired,
    };

const _$ColumnConfirmConfirmFieldsEnumMap = {
  ColumnConfirmConfirmFields.energyKcal: 'energy_kcal',
  ColumnConfirmConfirmFields.proteinG: 'protein_g',
  ColumnConfirmConfirmFields.carbsG: 'carbs_g',
  ColumnConfirmConfirmFields.sugarsG: 'sugars_g',
  ColumnConfirmConfirmFields.fatG: 'fat_g',
  ColumnConfirmConfirmFields.satFatG: 'sat_fat_g',
  ColumnConfirmConfirmFields.fiberG: 'fiber_g',
  ColumnConfirmConfirmFields.saltG: 'salt_g',
  ColumnConfirmConfirmFields.sodiumMg: 'sodium_mg',
  ColumnConfirmConfirmFields.servingSizeG: 'serving_size_g',
  ColumnConfirmConfirmFields.$unknown: r'$unknown',
};
