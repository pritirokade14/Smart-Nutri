// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Which type suggested it (display only)
@JsonEnum()
enum PrefillChangeReason {
  @JsonValue('health_condition')
  healthCondition('health_condition'),
  @JsonValue('family')
  family('family'),
  @JsonValue('weight_loss')
  weightLoss('weight_loss'),
  @JsonValue('gym')
  gym('gym'),
  @JsonValue('allergy_diet')
  allergyDiet('allergy_diet'),
  @JsonValue('eat_better')
  eatBetter('eat_better'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const PrefillChangeReason(this.json);

  factory PrefillChangeReason.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<PrefillChangeReason> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
