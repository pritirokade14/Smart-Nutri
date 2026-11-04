// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'better_side.dart';

part 'compare_better.g.dart';

/// Which side is better: lower energy, sugars, salt and saturated fat; higher protein and.
/// fibre; grade A best; higher protein per serving and per 100 kcal; lower sugars per serving.
/// ``unknown`` when either side has no value (never a win).
@JsonSerializable()
class CompareBetter {
  const CompareBetter({
    required this.energyKcal,
    required this.fiberG,
    required this.grade,
    required this.proteinG,
    required this.proteinPer100kcal,
    required this.proteinPerServingG,
    required this.saltG,
    required this.satFatG,
    required this.sugarsG,
    required this.sugarsPerServingG,
  });

  factory CompareBetter.fromJson(Map<String, Object?> json) =>
      _$CompareBetterFromJson(json);

  @JsonKey(name: 'energy_kcal')
  final BetterSide energyKcal;
  @JsonKey(name: 'fiber_g')
  final BetterSide fiberG;
  final BetterSide grade;
  @JsonKey(name: 'protein_g')
  final BetterSide proteinG;
  @JsonKey(name: 'protein_per_100kcal')
  final BetterSide proteinPer100kcal;
  @JsonKey(name: 'protein_per_serving_g')
  final BetterSide proteinPerServingG;
  @JsonKey(name: 'salt_g')
  final BetterSide saltG;
  @JsonKey(name: 'sat_fat_g')
  final BetterSide satFatG;
  @JsonKey(name: 'sugars_g')
  final BetterSide sugarsG;
  @JsonKey(name: 'sugars_per_serving_g')
  final BetterSide sugarsPerServingG;

  Map<String, Object?> toJson() => _$CompareBetterToJson(this);
}
