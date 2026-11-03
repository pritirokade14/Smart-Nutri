// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// no_better_found also when every better product is avoid for the member; source_protein_unknown: sort=protein and the source has no protein per 100 kcal
@JsonEnum()
enum AlternativesOutReason {
  @JsonValue('ok')
  ok('ok'),
  @JsonValue('no_category')
  noCategory('no_category'),
  @JsonValue('no_better_found')
  noBetterFound('no_better_found'),
  @JsonValue('source_ungraded')
  sourceUngraded('source_ungraded'),
  @JsonValue('source_protein_unknown')
  sourceProteinUnknown('source_protein_unknown'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const AlternativesOutReason(this.json);

  factory AlternativesOutReason.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<AlternativesOutReason> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
