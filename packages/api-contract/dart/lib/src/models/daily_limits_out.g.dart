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
      proteinBasis: json['protein_basis'] == null
          ? null
          : DailyLimitsOutProteinBasis.fromJson(
              json['protein_basis'] as String,
            ),
      proteinTargetStatus: json['protein_target_status'] == null
          ? null
          : DailyLimitsOutProteinTargetStatus.fromJson(
              json['protein_target_status'] as String,
            ),
    );

Map<String, dynamic> _$DailyLimitsOutToJson(
  DailyLimitsOut instance,
) => <String, dynamic>{
  'kcal': instance.kcal,
  'protein_basis': _$DailyLimitsOutProteinBasisEnumMap[instance.proteinBasis],
  'protein_g_per_kg': instance.proteinGPerKg,
  'protein_target_g': instance.proteinTargetG,
  'protein_target_status':
      _$DailyLimitsOutProteinTargetStatusEnumMap[instance.proteinTargetStatus],
  'salt_g': instance.saltG,
  'sugar_g': instance.sugarG,
};

const _$DailyLimitsOutProteinBasisEnumMap = {
  DailyLimitsOutProteinBasis.leanMass: 'lean_mass',
  DailyLimitsOutProteinBasis.adjustedWeight: 'adjusted_weight',
  DailyLimitsOutProteinBasis.actualWeight: 'actual_weight',
  DailyLimitsOutProteinBasis.$unknown: r'$unknown',
};

const _$DailyLimitsOutProteinTargetStatusEnumMap = {
  DailyLimitsOutProteinTargetStatus.ready: 'ready',
  DailyLimitsOutProteinTargetStatus.needsBodyData: 'needs_body_data',
  DailyLimitsOutProteinTargetStatus.notAvailableMinor: 'not_available_minor',
  DailyLimitsOutProteinTargetStatus.pausedPregnancy: 'paused_pregnancy',
  DailyLimitsOutProteinTargetStatus.$unknown: r'$unknown',
};
