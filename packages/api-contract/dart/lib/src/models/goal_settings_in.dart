// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'goal_settings_in_activity_level.dart';
import 'goal_settings_in_direction.dart';
import 'goal_settings_in_energy_mode.dart';
import 'goal_settings_in_numbers_display.dart';
import 'goal_settings_in_sex_reference.dart';
import 'goal_settings_in_summary_view.dart';

part 'goal_settings_in.g.dart';

/// Spec 6.1. `member_id` is optional (the primary). `rate_pct_bw_per_week` must be one of.
/// the YAML options for the direction and is null for `maintain`; omitted means the default.
@JsonSerializable()
class GoalSettingsIn {
  const GoalSettingsIn({
    required this.activityLevel,
    required this.direction,
    required this.pregnantOrBreastfeeding,
    this.fatPctEnergy,
    this.memberId,
    this.ratePctBwPerWeek,
    this.sexReference,
    this.targetWeightKg,
    this.energyMode = GoalSettingsInEnergyMode.formula,
    this.numbersDisplay = GoalSettingsInNumbersDisplay.valueShow,
    this.summaryView = GoalSettingsInSummaryView.remaining,
  });

  factory GoalSettingsIn.fromJson(Map<String, Object?> json) =>
      _$GoalSettingsInFromJson(json);

  @JsonKey(name: 'activity_level')
  final GoalSettingsInActivityLevel activityLevel;
  final GoalSettingsInDirection direction;
  @JsonKey(name: 'energy_mode')
  final GoalSettingsInEnergyMode energyMode;
  @JsonKey(name: 'fat_pct_energy')
  final num? fatPctEnergy;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'numbers_display')
  final GoalSettingsInNumbersDisplay numbersDisplay;
  @JsonKey(name: 'pregnant_or_breastfeeding')
  final bool pregnantOrBreastfeeding;
  @JsonKey(name: 'rate_pct_bw_per_week')
  final num? ratePctBwPerWeek;
  @JsonKey(name: 'sex_reference')
  final GoalSettingsInSexReference? sexReference;
  @JsonKey(name: 'summary_view')
  final GoalSettingsInSummaryView summaryView;
  @JsonKey(name: 'target_weight_kg')
  final num? targetWeightKg;

  Map<String, Object?> toJson() => _$GoalSettingsInToJson(this);
}
