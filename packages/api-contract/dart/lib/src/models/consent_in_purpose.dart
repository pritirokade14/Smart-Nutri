// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum ConsentInPurpose {
  @JsonValue('terms')
  terms('terms'),
  @JsonValue('health_data')
  healthData('health_data'),
  @JsonValue('ai_processing')
  aiProcessing('ai_processing'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ConsentInPurpose(this.json);

  factory ConsentInPurpose.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ConsentInPurpose> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
