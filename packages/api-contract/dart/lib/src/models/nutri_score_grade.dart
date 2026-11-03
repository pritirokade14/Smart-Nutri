// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Nutri-Score grade, calculated by SmartNutri (never an FSSAI rating).
@JsonEnum()
enum NutriScoreGrade {
  @JsonValue('A')
  a('A'),
  @JsonValue('B')
  b('B'),
  @JsonValue('C')
  c('C'),
  @JsonValue('D')
  d('D'),
  @JsonValue('E')
  e('E'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const NutriScoreGrade(this.json);

  factory NutriScoreGrade.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<NutriScoreGrade> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
