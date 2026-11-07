// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'body_data_in.dart';
import 'targets_preview_in_activity_level.dart';
import 'targets_preview_in_direction.dart';
import 'targets_preview_in_energy_mode.dart';
import 'targets_preview_in_numbers_display.dart';
import 'targets_preview_in_sex_reference.dart';
import 'targets_preview_in_summary_view.dart';

part 'targets_preview_in.g.dart';

@JsonSerializable()
class TargetsPreviewIn {
  const TargetsPreviewIn({
    required this.activityLevel,
    required this.direction,
    required this.pregnantOrBreastfeeding,
    this.energyMode = TargetsPreviewInEnergyMode.formula,
    this.numbersDisplay = TargetsPreviewInNumbersDisplay.valueShow,
    this.summaryView = TargetsPreviewInSummaryView.remaining,
    this.body,
    this.fatPctEnergy,
    this.memberId,
    this.ratePctBwPerWeek,
    this.sexReference,
    this.targetWeightKg,
  });

  factory TargetsPreviewIn.fromJson(Map<String, Object?> json) =>
      _$TargetsPreviewInFromJson(json);

  @JsonKey(name: 'activity_level')
  final TargetsPreviewInActivityLevel activityLevel;
  final BodyDataIn? body;
  final TargetsPreviewInDirection direction;
  @JsonKey(name: 'energy_mode')
  final TargetsPreviewInEnergyMode energyMode;
  @JsonKey(name: 'fat_pct_energy')
  final num? fatPctEnergy;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'numbers_display')
  final TargetsPreviewInNumbersDisplay numbersDisplay;
  @JsonKey(name: 'pregnant_or_breastfeeding')
  final bool pregnantOrBreastfeeding;
  @JsonKey(name: 'rate_pct_bw_per_week')
  final num? ratePctBwPerWeek;
  @JsonKey(name: 'sex_reference')
  final TargetsPreviewInSexReference? sexReference;
  @JsonKey(name: 'summary_view')
  final TargetsPreviewInSummaryView summaryView;
  @JsonKey(name: 'target_weight_kg')
  final num? targetWeightKg;

  Map<String, Object?> toJson() => _$TargetsPreviewInToJson(this);
}
