// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum UserTypesInTypes {
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

  const UserTypesInTypes(this.json);

  factory UserTypesInTypes.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<UserTypesInTypes> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
