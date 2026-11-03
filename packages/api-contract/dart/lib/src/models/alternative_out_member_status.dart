// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// The rules engine's verdict for member_id (only when member_id is given)
@JsonEnum()
enum AlternativeOutMemberStatus {
  @JsonValue('ok')
  ok('ok'),
  @JsonValue('caution')
  caution('caution'),
  @JsonValue('unknown')
  unknown('unknown'),
  @JsonValue('avoid')
  avoid('avoid'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const AlternativeOutMemberStatus(this.json);

  factory AlternativeOutMemberStatus.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<AlternativeOutMemberStatus> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
