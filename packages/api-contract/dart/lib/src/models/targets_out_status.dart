// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum TargetsOutStatus {
  @JsonValue('ready')
  ready('ready'),
  @JsonValue('needs_body_data')
  needsBodyData('needs_body_data'),
  @JsonValue('not_available_minor')
  notAvailableMinor('not_available_minor'),
  @JsonValue('paused_pregnancy')
  pausedPregnancy('paused_pregnancy'),
  @JsonValue('none')
  none('none'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const TargetsOutStatus(this.json);

  factory TargetsOutStatus.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<TargetsOutStatus> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
