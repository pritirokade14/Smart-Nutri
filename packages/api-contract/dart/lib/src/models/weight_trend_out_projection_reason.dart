// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum WeightTrendOutProjectionReason {
  @JsonValue('ready')
  ready('ready'),
  @JsonValue('too_few_weigh_ins')
  tooFewWeighIns('too_few_weigh_ins'),
  @JsonValue('moving_away')
  movingAway('moving_away'),
  @JsonValue('no_target')
  noTarget('no_target'),
  @JsonValue('too_far')
  tooFar('too_far'),
  @JsonValue('reached')
  reached('reached'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const WeightTrendOutProjectionReason(this.json);

  factory WeightTrendOutProjectionReason.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<WeightTrendOutProjectionReason> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
