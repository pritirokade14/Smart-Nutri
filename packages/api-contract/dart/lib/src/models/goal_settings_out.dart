// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'goal_settings_out_activity_level.dart';
import 'goal_settings_out_direction.dart';
import 'goal_settings_out_energy_mode.dart';
import 'goal_settings_out_numbers_display.dart';
import 'goal_settings_out_sex_reference.dart';
import 'goal_settings_out_summary_view.dart';

part 'goal_settings_out.g.dart';

@JsonSerializable()
class GoalSettingsOut {
  const GoalSettingsOut({
    required this.activityLevel,
    required this.direction,
    required this.memberId,
    required this.pregnantOrBreastfeeding,
    required this.updatedAt,
    this.fatPctEnergy,
    this.ratePctBwPerWeek,
    this.sexReference,
    this.targetWeightKg,
    this.energyMode = GoalSettingsOutEnergyMode.formula,
    this.numbersDisplay = GoalSettingsOutNumbersDisplay.valueShow,
    this.summaryView = GoalSettingsOutSummaryView.remaining,
  });

  factory GoalSettingsOut.fromJson(Map<String, Object?> json) =>
      _$GoalSettingsOutFromJson(json);

  @JsonKey(name: 'activity_level')
  final GoalSettingsOutActivityLevel activityLevel;
  final GoalSettingsOutDirection direction;
  @JsonKey(name: 'energy_mode')
  final GoalSettingsOutEnergyMode energyMode;
  @JsonKey(name: 'fat_pct_energy')
  final num? fatPctEnergy;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'numbers_display')
  final GoalSettingsOutNumbersDisplay numbersDisplay;
  @JsonKey(name: 'pregnant_or_breastfeeding')
  final bool pregnantOrBreastfeeding;
  @JsonKey(name: 'rate_pct_bw_per_week')
  final num? ratePctBwPerWeek;
  @JsonKey(name: 'sex_reference')
  final GoalSettingsOutSexReference? sexReference;
  @JsonKey(name: 'summary_view')
  final GoalSettingsOutSummaryView summaryView;
  @JsonKey(name: 'target_weight_kg')
  final num? targetWeightKg;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$GoalSettingsOutToJson(this);
}
