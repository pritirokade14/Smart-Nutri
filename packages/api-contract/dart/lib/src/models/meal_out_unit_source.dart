// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// How `grams` was worked out from the unit when logged: `grams` (exact: grams, millilitres or a label serving), `portion` (a per-food weight, ours or the account's own) or `density` (a volume converted through a density). Clients mark `portion` and `density` as approximate (≈). null on older entries
@JsonEnum()
enum MealOutUnitSource {
  @JsonValue('grams')
  grams('grams'),
  @JsonValue('portion')
  portion('portion'),
  @JsonValue('density')
  density('density'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const MealOutUnitSource(this.json);

  factory MealOutUnitSource.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<MealOutUnitSource> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
