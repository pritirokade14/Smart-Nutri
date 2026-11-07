// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum WeightTrendOutDays {
  @JsonValue(30)
  value30(30),
  @JsonValue(90)
  value90(90),
  @JsonValue(365)
  value365(365),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const WeightTrendOutDays(this.json);

  factory WeightTrendOutDays.fromJson(int json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final int? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<WeightTrendOutDays> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
