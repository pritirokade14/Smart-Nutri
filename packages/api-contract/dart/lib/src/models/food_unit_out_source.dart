// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum FoodUnitOutSource {
  @JsonValue('mass')
  mass('mass'),
  @JsonValue('serving')
  serving('serving'),
  @JsonValue('portion_user')
  portionUser('portion_user'),
  @JsonValue('portion_global')
  portionGlobal('portion_global'),
  @JsonValue('density')
  density('density'),
  @JsonValue('volume_basis')
  volumeBasis('volume_basis'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FoodUnitOutSource(this.json);

  factory FoodUnitOutSource.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FoodUnitOutSource> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
