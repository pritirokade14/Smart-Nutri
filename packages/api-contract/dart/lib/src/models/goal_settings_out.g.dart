// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'goal_settings_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GoalSettingsOut _$GoalSettingsOutFromJson(Map<String, dynamic> json) =>
    GoalSettingsOut(
      activityLevel: GoalSettingsOutActivityLevel.fromJson(
        json['activity_level'] as String,
      ),
      direction: GoalSettingsOutDirection.fromJson(json['direction'] as String),
      memberId: json['member_id'] as String,
      pregnantOrBreastfeeding: json['pregnant_or_breastfeeding'] as bool,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      fatPctEnergy: json['fat_pct_energy'] as num?,
      ratePctBwPerWeek: json['rate_pct_bw_per_week'] as num?,
      sexReference: json['sex_reference'] == null
          ? null
          : GoalSettingsOutSexReference.fromJson(
              json['sex_reference'] as String,
            ),
      targetWeightKg: json['target_weight_kg'] as num?,
      energyMode: json['energy_mode'] == null
          ? GoalSettingsOutEnergyMode.formula
          : GoalSettingsOutEnergyMode.fromJson(json['energy_mode'] as String),
      numbersDisplay: json['numbers_display'] == null
          ? GoalSettingsOutNumbersDisplay.valueShow
          : GoalSettingsOutNumbersDisplay.fromJson(
              json['numbers_display'] as String,
            ),
      summaryView: json['summary_view'] == null
          ? GoalSettingsOutSummaryView.remaining
          : GoalSettingsOutSummaryView.fromJson(json['summary_view'] as String),
    );

Map<String, dynamic> _$GoalSettingsOutToJson(
  GoalSettingsOut instance,
) => <String, dynamic>{
  'activity_level':
      _$GoalSettingsOutActivityLevelEnumMap[instance.activityLevel]!,
  'direction': _$GoalSettingsOutDirectionEnumMap[instance.direction]!,
  'energy_mode': _$GoalSettingsOutEnergyModeEnumMap[instance.energyMode]!,
  'fat_pct_energy': instance.fatPctEnergy,
  'member_id': instance.memberId,
  'numbers_display':
      _$GoalSettingsOutNumbersDisplayEnumMap[instance.numbersDisplay]!,
  'pregnant_or_breastfeeding': instance.pregnantOrBreastfeeding,
  'rate_pct_bw_per_week': instance.ratePctBwPerWeek,
  'sex_reference': _$GoalSettingsOutSexReferenceEnumMap[instance.sexReference],
  'summary_view': _$GoalSettingsOutSummaryViewEnumMap[instance.summaryView]!,
  'target_weight_kg': instance.targetWeightKg,
  'updated_at': instance.updatedAt.toIso8601String(),
};

const _$GoalSettingsOutActivityLevelEnumMap = {
  GoalSettingsOutActivityLevel.sedentary: 'sedentary',
  GoalSettingsOutActivityLevel.light: 'light',
  GoalSettingsOutActivityLevel.moderate: 'moderate',
  GoalSettingsOutActivityLevel.very: 'very',
  GoalSettingsOutActivityLevel.$unknown: r'$unknown',
};

const _$GoalSettingsOutDirectionEnumMap = {
  GoalSettingsOutDirection.lose: 'lose',
  GoalSettingsOutDirection.maintain: 'maintain',
  GoalSettingsOutDirection.gain: 'gain',
  GoalSettingsOutDirection.$unknown: r'$unknown',
};

const _$GoalSettingsOutEnergyModeEnumMap = {
  GoalSettingsOutEnergyMode.formula: 'formula',
  GoalSettingsOutEnergyMode.adaptive: 'adaptive',
  GoalSettingsOutEnergyMode.$unknown: r'$unknown',
};

const _$GoalSettingsOutNumbersDisplayEnumMap = {
  GoalSettingsOutNumbersDisplay.valueShow: 'show',
  GoalSettingsOutNumbersDisplay.hideEnergy: 'hide_energy',
  GoalSettingsOutNumbersDisplay.hideAll: 'hide_all',
  GoalSettingsOutNumbersDisplay.$unknown: r'$unknown',
};

const _$GoalSettingsOutSexReferenceEnumMap = {
  GoalSettingsOutSexReference.male: 'male',
  GoalSettingsOutSexReference.female: 'female',
  GoalSettingsOutSexReference.average: 'average',
  GoalSettingsOutSexReference.$unknown: r'$unknown',
};

const _$GoalSettingsOutSummaryViewEnumMap = {
  GoalSettingsOutSummaryView.remaining: 'remaining',
  GoalSettingsOutSummaryView.consumed: 'consumed',
  GoalSettingsOutSummaryView.$unknown: r'$unknown',
};
