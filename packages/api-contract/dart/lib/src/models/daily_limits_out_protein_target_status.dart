// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// null = the legacy rule applied (no goal settings, or health_data not active). Otherwise the daily-targets status; anything but `ready` means no protein target (not_available_minor, paused_pregnancy, needs_body_data)
@JsonEnum()
enum DailyLimitsOutProteinTargetStatus {
  @JsonValue('ready')
  ready('ready'),
  @JsonValue('needs_body_data')
  needsBodyData('needs_body_data'),
  @JsonValue('not_available_minor')
  notAvailableMinor('not_available_minor'),
  @JsonValue('paused_pregnancy')
  pausedPregnancy('paused_pregnancy'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const DailyLimitsOutProteinTargetStatus(this.json);

  factory DailyLimitsOutProteinTargetStatus.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<DailyLimitsOutProteinTargetStatus> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
