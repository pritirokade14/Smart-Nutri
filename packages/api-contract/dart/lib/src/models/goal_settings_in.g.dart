// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'goal_settings_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GoalSettingsIn _$GoalSettingsInFromJson(Map<String, dynamic> json) =>
    GoalSettingsIn(
      activityLevel: GoalSettingsInActivityLevel.fromJson(
        json['activity_level'] as String,
      ),
      direction: GoalSettingsInDirection.fromJson(json['direction'] as String),
      pregnantOrBreastfeeding: json['pregnant_or_breastfeeding'] as bool,
      fatPctEnergy: json['fat_pct_energy'] as num?,
      memberId: json['member_id'] as String?,
      ratePctBwPerWeek: json['rate_pct_bw_per_week'] as num?,
      sexReference: json['sex_reference'] == null
          ? null
          : GoalSettingsInSexReference.fromJson(
              json['sex_reference'] as String,
            ),
      targetWeightKg: json['target_weight_kg'] as num?,
      energyMode: json['energy_mode'] == null
          ? GoalSettingsInEnergyMode.formula
          : GoalSettingsInEnergyMode.fromJson(json['energy_mode'] as String),
      numbersDisplay: json['numbers_display'] == null
          ? GoalSettingsInNumbersDisplay.valueShow
          : GoalSettingsInNumbersDisplay.fromJson(
              json['numbers_display'] as String,
            ),
      summaryView: json['summary_view'] == null
          ? GoalSettingsInSummaryView.remaining
          : GoalSettingsInSummaryView.fromJson(json['summary_view'] as String),
    );

Map<String, dynamic> _$GoalSettingsInToJson(
  GoalSettingsIn instance,
) => <String, dynamic>{
  'activity_level':
      _$GoalSettingsInActivityLevelEnumMap[instance.activityLevel]!,
  'direction': _$GoalSettingsInDirectionEnumMap[instance.direction]!,
  'energy_mode': _$GoalSettingsInEnergyModeEnumMap[instance.energyMode]!,
  'fat_pct_energy': instance.fatPctEnergy,
  'member_id': instance.memberId,
  'numbers_display':
      _$GoalSettingsInNumbersDisplayEnumMap[instance.numbersDisplay]!,
  'pregnant_or_breastfeeding': instance.pregnantOrBreastfeeding,
  'rate_pct_bw_per_week': instance.ratePctBwPerWeek,
  'sex_reference': _$GoalSettingsInSexReferenceEnumMap[instance.sexReference],
  'summary_view': _$GoalSettingsInSummaryViewEnumMap[instance.summaryView]!,
  'target_weight_kg': instance.targetWeightKg,
};

const _$GoalSettingsInActivityLevelEnumMap = {
  GoalSettingsInActivityLevel.sedentary: 'sedentary',
  GoalSettingsInActivityLevel.light: 'light',
  GoalSettingsInActivityLevel.moderate: 'moderate',
  GoalSettingsInActivityLevel.very: 'very',
  GoalSettingsInActivityLevel.$unknown: r'$unknown',
};

const _$GoalSettingsInDirectionEnumMap = {
  GoalSettingsInDirection.lose: 'lose',
  GoalSettingsInDirection.maintain: 'maintain',
  GoalSettingsInDirection.gain: 'gain',
  GoalSettingsInDirection.$unknown: r'$unknown',
};

const _$GoalSettingsInEnergyModeEnumMap = {
  GoalSettingsInEnergyMode.formula: 'formula',
  GoalSettingsInEnergyMode.adaptive: 'adaptive',
  GoalSettingsInEnergyMode.$unknown: r'$unknown',
};

const _$GoalSettingsInNumbersDisplayEnumMap = {
  GoalSettingsInNumbersDisplay.valueShow: 'show',
  GoalSettingsInNumbersDisplay.hideEnergy: 'hide_energy',
  GoalSettingsInNumbersDisplay.hideAll: 'hide_all',
  GoalSettingsInNumbersDisplay.$unknown: r'$unknown',
};

const _$GoalSettingsInSexReferenceEnumMap = {
  GoalSettingsInSexReference.male: 'male',
  GoalSettingsInSexReference.female: 'female',
  GoalSettingsInSexReference.average: 'average',
  GoalSettingsInSexReference.$unknown: r'$unknown',
};

const _$GoalSettingsInSummaryViewEnumMap = {
  GoalSettingsInSummaryView.remaining: 'remaining',
  GoalSettingsInSummaryView.consumed: 'consumed',
  GoalSettingsInSummaryView.$unknown: r'$unknown',
};
