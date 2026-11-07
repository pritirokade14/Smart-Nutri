// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Which weight protein_g_per_kg applies to: lean_mass, adjusted_weight or actual_weight (the legacy weight x g/kg rule, whenever it gives a target). Null whenever protein_target_g is null. Display only (the protein.guide_* copy)
@JsonEnum()
enum DailyLimitsOutProteinBasis {
  @JsonValue('lean_mass')
  leanMass('lean_mass'),
  @JsonValue('adjusted_weight')
  adjustedWeight('adjusted_weight'),
  @JsonValue('actual_weight')
  actualWeight('actual_weight'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const DailyLimitsOutProteinBasis(this.json);

  factory DailyLimitsOutProteinBasis.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<DailyLimitsOutProteinBasis> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
