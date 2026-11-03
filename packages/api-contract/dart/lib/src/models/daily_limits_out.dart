// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'daily_limits_out.g.dart';

/// Per DAY, from the rules engine (thresholds.yaml, pending clinician review).
@JsonSerializable()
class DailyLimitsOut {
  const DailyLimitsOut({
    required this.kcal,
    required this.proteinTargetG,
    required this.saltG,
    required this.sugarG,
  });

  factory DailyLimitsOut.fromJson(Map<String, Object?> json) =>
      _$DailyLimitsOutFromJson(json);

  /// Always null in v1 (no personal energy target)
  final num? kcal;

  /// A target, not a limit; null without weight
  @JsonKey(name: 'protein_target_g')
  final num? proteinTargetG;
  @JsonKey(name: 'salt_g')
  final num? saltG;
  @JsonKey(name: 'sugar_g')
  final num? sugarG;

  Map<String, Object?> toJson() => _$DailyLimitsOutToJson(this);
}
