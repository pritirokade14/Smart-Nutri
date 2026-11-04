// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Search order: ``relevance`` (ours first, then Open Food Facts) or ``protein`` (most.
/// protein per 100 kcal first, unknown last, never avoid for the member).
@JsonEnum()
enum SearchSort {
  @JsonValue('relevance')
  relevance('relevance'),
  @JsonValue('protein')
  protein('protein'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const SearchSort(this.json);

  factory SearchSort.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<SearchSort> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
