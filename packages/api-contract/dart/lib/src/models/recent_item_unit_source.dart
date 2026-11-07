// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// How `grams` came from the unit; `portion` and `density` are approximate (≈)
@JsonEnum()
enum RecentItemUnitSource {
  @JsonValue('grams')
  grams('grams'),
  @JsonValue('portion')
  portion('portion'),
  @JsonValue('density')
  density('density'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const RecentItemUnitSource(this.json);

  factory RecentItemUnitSource.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<RecentItemUnitSource> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
