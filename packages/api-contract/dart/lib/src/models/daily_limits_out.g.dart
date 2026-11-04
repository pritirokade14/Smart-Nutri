// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daily_limits_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DailyLimitsOut _$DailyLimitsOutFromJson(Map<String, dynamic> json) =>
    DailyLimitsOut(
      kcal: json['kcal'] as num?,
      proteinGPerKg: json['protein_g_per_kg'] as num?,
      proteinTargetG: json['protein_target_g'] as num?,
      saltG: json['salt_g'] as num?,
      sugarG: json['sugar_g'] as num?,
    );

Map<String, dynamic> _$DailyLimitsOutToJson(DailyLimitsOut instance) =>
    <String, dynamic>{
      'kcal': instance.kcal,
      'protein_g_per_kg': instance.proteinGPerKg,
      'protein_target_g': instance.proteinTargetG,
      'salt_g': instance.saltG,
      'sugar_g': instance.sugarG,
    };
