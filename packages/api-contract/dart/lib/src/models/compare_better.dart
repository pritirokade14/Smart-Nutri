// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'better_side.dart';

part 'compare_better.g.dart';

/// Which side is better: lower energy, sugars, salt and saturated fat; higher protein and.
/// fibre; grade A best. ``unknown`` when either side has no value (never a win).
@JsonSerializable()
class CompareBetter {
  const CompareBetter({
    required this.energyKcal,
    required this.fiberG,
    required this.grade,
    required this.proteinG,
    required this.saltG,
    required this.satFatG,
    required this.sugarsG,
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
  @JsonKey(name: 'salt_g')
  final BetterSide saltG;
  @JsonKey(name: 'sat_fat_g')
  final BetterSide satFatG;
  @JsonKey(name: 'sugars_g')
  final BetterSide sugarsG;

  Map<String, Object?> toJson() => _$CompareBetterToJson(this);
}
