// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// The unit of `nutrients.sodium_mg`: null means mg (the unit is printed, or this is a manual entry in mg). `g` is converted to mg by the server. Send the user's explicit pick (`mg` or `g`, never null) when the scan draft has `unit_unconfirmed:<basis>.sodium_mg` and sodium is not null; a non-null unit confirms sodium.
@JsonEnum()
enum ProductCreateSodiumUnit {
  @JsonValue('mg')
  mg('mg'),
  @JsonValue('g')
  g('g'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ProductCreateSodiumUnit(this.json);

  factory ProductCreateSodiumUnit.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ProductCreateSodiumUnit> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
