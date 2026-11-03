// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum ProductDraftCategory {
  @JsonValue('general')
  general('general'),
  @JsonValue('beverage')
  beverage('beverage'),
  @JsonValue('water')
  water('water'),
  @JsonValue('cheese')
  cheese('cheese'),
  @JsonValue('fat')
  fat('fat'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ProductDraftCategory(this.json);

  factory ProductDraftCategory.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ProductDraftCategory> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
