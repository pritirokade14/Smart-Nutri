// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Required: the user's explicit choice (drinks are judged on drink limits).
@JsonEnum()
enum ProductCreateCategory {
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
  @JsonValue('supplement')
  supplement('supplement'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ProductCreateCategory(this.json);

  factory ProductCreateCategory.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<ProductCreateCategory> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
