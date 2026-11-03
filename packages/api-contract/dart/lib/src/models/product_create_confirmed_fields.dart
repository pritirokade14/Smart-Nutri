// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum ProductCreateConfirmedFields {
  @JsonValue('energy_kcal')
  energyKcal('energy_kcal'),
  @JsonValue('protein_g')
  proteinG('protein_g'),
  @JsonValue('carbs_g')
  carbsG('carbs_g'),
  @JsonValue('sugars_g')
  sugarsG('sugars_g'),
  @JsonValue('fat_g')
  fatG('fat_g'),
  @JsonValue('sat_fat_g')
  satFatG('sat_fat_g'),
  @JsonValue('fiber_g')
  fiberG('fiber_g'),
  @JsonValue('salt_g')
  saltG('salt_g'),
  @JsonValue('sodium_mg')
  sodiumMg('sodium_mg'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ProductCreateConfirmedFields(this.json);

  factory ProductCreateConfirmedFields.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ProductCreateConfirmedFields> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
