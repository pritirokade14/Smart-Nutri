// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum PrefillChangeField {
  @JsonValue('conditions')
  conditions('conditions'),
  @JsonValue('allergens')
  allergens('allergens'),
  @JsonValue('diet')
  diet('diet'),
  @JsonValue('goal')
  goal('goal'),
  @JsonValue('custom_alerts')
  customAlerts('custom_alerts'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const PrefillChangeField(this.json);

  factory PrefillChangeField.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<PrefillChangeField> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
