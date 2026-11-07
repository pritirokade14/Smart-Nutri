// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum MealPatchUnit {
  @JsonValue('g')
  g('g'),
  @JsonValue('ml')
  ml('ml'),
  @JsonValue('serving')
  serving('serving'),
  @JsonValue('piece')
  piece('piece'),
  @JsonValue('piece_small')
  pieceSmall('piece_small'),
  @JsonValue('piece_medium')
  pieceMedium('piece_medium'),
  @JsonValue('piece_large')
  pieceLarge('piece_large'),
  @JsonValue('roti')
  roti('roti'),
  @JsonValue('slice')
  slice('slice'),
  @JsonValue('katori')
  katori('katori'),
  @JsonValue('katori_small')
  katoriSmall('katori_small'),
  @JsonValue('katori_medium')
  katoriMedium('katori_medium'),
  @JsonValue('katori_large')
  katoriLarge('katori_large'),
  @JsonValue('cup')
  cup('cup'),
  @JsonValue('glass')
  glass('glass'),
  @JsonValue('tbsp')
  tbsp('tbsp'),
  @JsonValue('tsp')
  tsp('tsp'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const MealPatchUnit(this.json);

  factory MealPatchUnit.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<MealPatchUnit> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
