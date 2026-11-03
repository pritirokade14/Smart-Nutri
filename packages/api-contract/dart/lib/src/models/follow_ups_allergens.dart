// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum FollowUpsAllergens {
  @JsonValue('milk')
  milk('milk'),
  @JsonValue('peanut')
  peanut('peanut'),
  @JsonValue('gluten')
  gluten('gluten'),
  @JsonValue('soy')
  soy('soy'),
  @JsonValue('egg')
  egg('egg'),
  @JsonValue('tree_nut')
  treeNut('tree_nut'),
  @JsonValue('sesame')
  sesame('sesame'),
  @JsonValue('fish')
  fish('fish'),
  @JsonValue('crustacean')
  crustacean('crustacean'),
  @JsonValue('mustard')
  mustard('mustard'),
  @JsonValue('sulphite')
  sulphite('sulphite'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FollowUpsAllergens(this.json);

  factory FollowUpsAllergens.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<FollowUpsAllergens> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
