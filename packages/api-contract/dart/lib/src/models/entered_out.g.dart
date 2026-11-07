// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'entered_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EnteredOut _$EnteredOutFromJson(Map<String, dynamic> json) => EnteredOut(
  nutrients: CustomNutrientsIn.fromJson(
    json['nutrients'] as Map<String, dynamic>,
  ),
  servingG: json['serving_g'] as num?,
  valuesPer: EnteredOutValuesPer.fromJson(json['values_per'] as String),
);

Map<String, dynamic> _$EnteredOutToJson(EnteredOut instance) =>
    <String, dynamic>{
      'nutrients': instance.nutrients,
      'serving_g': instance.servingG,
      'values_per': _$EnteredOutValuesPerEnumMap[instance.valuesPer]!,
    };

const _$EnteredOutValuesPerEnumMap = {
  EnteredOutValuesPer.value100: '100',
  EnteredOutValuesPer.serving: 'serving',
  EnteredOutValuesPer.$unknown: r'$unknown',
};
