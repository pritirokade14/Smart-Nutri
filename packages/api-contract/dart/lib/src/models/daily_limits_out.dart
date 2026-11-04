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
    required this.proteinGPerKg,
    required this.proteinTargetG,
    required this.saltG,
    required this.sugarG,
  });

  factory DailyLimitsOut.fromJson(Map<String, Object?> json) =>
      _$DailyLimitsOutFromJson(json);

  /// Always null in v1 (no personal energy target)
  final num? kcal;

  /// The g per kg body weight per day the protein target was computed with (thresholds.yaml, pending clinician review), for the protein.guide copy. Null whenever protein_target_g is null. Display only; never compute a target on the client
  @JsonKey(name: 'protein_g_per_kg')
  final num? proteinGPerKg;

  /// A target, not a limit. Adults (18+) with a weight only; null for children, adolescents, an unknown age or no weight
  @JsonKey(name: 'protein_target_g')
  final num? proteinTargetG;
  @JsonKey(name: 'salt_g')
  final num? saltG;
  @JsonKey(name: 'sugar_g')
  final num? sugarG;

  Map<String, Object?> toJson() => _$DailyLimitsOutToJson(this);
}
