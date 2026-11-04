// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum FollowUpsDiet {
  @JsonValue('veg')
  veg('veg'),
  @JsonValue('eggetarian')
  eggetarian('eggetarian'),
  @JsonValue('vegan')
  vegan('vegan'),
  @JsonValue('jain')
  jain('jain'),
  @JsonValue('non_veg')
  nonVeg('non_veg'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FollowUpsDiet(this.json);

  factory FollowUpsDiet.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FollowUpsDiet> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
