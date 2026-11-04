// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Alternatives order: ``grade`` (better Nutri-Score) or ``protein`` (more protein per.
/// 100 kcal, never avoid for the member, never a worse grade).
@JsonEnum()
enum AlternativesSort {
  @JsonValue('grade')
  grade('grade'),
  @JsonValue('protein')
  protein('protein'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const AlternativesSort(this.json);

  factory AlternativesSort.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<AlternativesSort> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
