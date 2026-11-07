// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// What ``id`` is: a generic food or dish (uuid), our own product (uuid) or an Open Food.
/// Facts product (the barcode).
@JsonEnum()
enum FoodKindPath {
  @JsonValue('food')
  food('food'),
  @JsonValue('product')
  product('product'),
  @JsonValue('off')
  off('off'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FoodKindPath(this.json);

  factory FoodKindPath.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FoodKindPath> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
