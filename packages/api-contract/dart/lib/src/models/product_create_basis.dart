// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Required: which printed column `nutrients` was transcribed from. `per_100g` means per 100 g or 100 ml; `per_serving` means per `serving_size_g`, and the server converts to per 100 g.
@JsonEnum()
enum ProductCreateBasis {
  @JsonValue('per_100g')
  per100g('per_100g'),
  @JsonValue('per_serving')
  perServing('per_serving'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ProductCreateBasis(this.json);

  factory ProductCreateBasis.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ProductCreateBasis> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
