// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum FavouriteItemOutSourceKind {
  @JsonValue('product')
  product('product'),
  @JsonValue('off')
  off('off'),
  @JsonValue('food')
  food('food'),
  @JsonValue('custom_food')
  customFood('custom_food'),
  @JsonValue('recipe')
  recipe('recipe'),
  @JsonValue('quick_add')
  quickAdd('quick_add'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FavouriteItemOutSourceKind(this.json);

  factory FavouriteItemOutSourceKind.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FavouriteItemOutSourceKind> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
