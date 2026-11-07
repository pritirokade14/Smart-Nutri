// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// The unit of `grams`: grams or millilitres (an ml-basis food)
@JsonEnum()
enum FavouriteItemOutBasis {
  @JsonValue('g')
  g('g'),
  @JsonValue('ml')
  ml('ml'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FavouriteItemOutBasis(this.json);

  factory FavouriteItemOutBasis.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FavouriteItemOutBasis> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
