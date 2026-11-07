// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'targets_preview_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TargetsPreviewIn _$TargetsPreviewInFromJson(
  Map<String, dynamic> json,
) => TargetsPreviewIn(
  activityLevel: TargetsPreviewInActivityLevel.fromJson(
    json['activity_level'] as String,
  ),
  direction: TargetsPreviewInDirection.fromJson(json['direction'] as String),
  pregnantOrBreastfeeding: json['pregnant_or_breastfeeding'] as bool,
  energyMode: json['energy_mode'] == null
      ? TargetsPreviewInEnergyMode.formula
      : TargetsPreviewInEnergyMode.fromJson(json['energy_mode'] as String),
  numbersDisplay: json['numbers_display'] == null
      ? TargetsPreviewInNumbersDisplay.valueShow
      : TargetsPreviewInNumbersDisplay.fromJson(
          json['numbers_display'] as String,
        ),
  summaryView: json['summary_view'] == null
      ? TargetsPreviewInSummaryView.remaining
      : TargetsPreviewInSummaryView.fromJson(json['summary_view'] as String),
  body: json['body'] == null
      ? null
      : BodyDataIn.fromJson(json['body'] as Map<String, dynamic>),
  fatPctEnergy: json['fat_pct_energy'] as num?,
  memberId: json['member_id'] as String?,
  ratePctBwPerWeek: json['rate_pct_bw_per_week'] as num?,
  sexReference: json['sex_reference'] == null
      ? null
      : TargetsPreviewInSexReference.fromJson(json['sex_reference'] as String),
  targetWeightKg: json['target_weight_kg'] as num?,
);

Map<String, dynamic> _$TargetsPreviewInToJson(
  TargetsPreviewIn instance,
) => <String, dynamic>{
  'activity_level':
      _$TargetsPreviewInActivityLevelEnumMap[instance.activityLevel]!,
  'body': instance.body,
  'direction': _$TargetsPreviewInDirectionEnumMap[instance.direction]!,
  'energy_mode': _$TargetsPreviewInEnergyModeEnumMap[instance.energyMode]!,
  'fat_pct_energy': instance.fatPctEnergy,
  'member_id': instance.memberId,
  'numbers_display':
      _$TargetsPreviewInNumbersDisplayEnumMap[instance.numbersDisplay]!,
  'pregnant_or_breastfeeding': instance.pregnantOrBreastfeeding,
  'rate_pct_bw_per_week': instance.ratePctBwPerWeek,
  'sex_reference': _$TargetsPreviewInSexReferenceEnumMap[instance.sexReference],
  'summary_view': _$TargetsPreviewInSummaryViewEnumMap[instance.summaryView]!,
  'target_weight_kg': instance.targetWeightKg,
};

const _$TargetsPreviewInActivityLevelEnumMap = {
  TargetsPreviewInActivityLevel.sedentary: 'sedentary',
  TargetsPreviewInActivityLevel.light: 'light',
  TargetsPreviewInActivityLevel.moderate: 'moderate',
  TargetsPreviewInActivityLevel.very: 'very',
  TargetsPreviewInActivityLevel.$unknown: r'$unknown',
};

const _$TargetsPreviewInDirectionEnumMap = {
  TargetsPreviewInDirection.lose: 'lose',
  TargetsPreviewInDirection.maintain: 'maintain',
  TargetsPreviewInDirection.gain: 'gain',
  TargetsPreviewInDirection.$unknown: r'$unknown',
};

const _$TargetsPreviewInEnergyModeEnumMap = {
  TargetsPreviewInEnergyMode.formula: 'formula',
  TargetsPreviewInEnergyMode.adaptive: 'adaptive',
  TargetsPreviewInEnergyMode.$unknown: r'$unknown',
};

const _$TargetsPreviewInNumbersDisplayEnumMap = {
  TargetsPreviewInNumbersDisplay.valueShow: 'show',
  TargetsPreviewInNumbersDisplay.hideEnergy: 'hide_energy',
  TargetsPreviewInNumbersDisplay.hideAll: 'hide_all',
  TargetsPreviewInNumbersDisplay.$unknown: r'$unknown',
};

const _$TargetsPreviewInSexReferenceEnumMap = {
  TargetsPreviewInSexReference.male: 'male',
  TargetsPreviewInSexReference.female: 'female',
  TargetsPreviewInSexReference.average: 'average',
  TargetsPreviewInSexReference.$unknown: r'$unknown',
};

const _$TargetsPreviewInSummaryViewEnumMap = {
  TargetsPreviewInSummaryView.remaining: 'remaining',
  TargetsPreviewInSummaryView.consumed: 'consumed',
  TargetsPreviewInSummaryView.$unknown: r'$unknown',
};
