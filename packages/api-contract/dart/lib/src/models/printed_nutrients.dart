// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'printed_nutrients.g.dart';

/// One nutrition-table column exactly as the pack prints it (see `ProductCreate.basis`).
///
/// Numbers only, no arithmetic: the server converts the basis and the sodium unit. A value.
/// not printed (or blanked by the user) is null, never 0. The nine engine fields are.
/// required (send null when not printed); `added_sugars_g` and `trans_fat_g` are optional.
/// and shown only, never engine inputs.
@JsonSerializable()
class PrintedNutrients {
  const PrintedNutrients({
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.fiberG,
    required this.proteinG,
    required this.saltG,
    required this.satFatG,
    required this.sodiumMg,
    required this.sugarsG,
    this.addedSugarsG,
    this.transFatG,
  });

  factory PrintedNutrients.fromJson(Map<String, Object?> json) =>
      _$PrintedNutrientsFromJson(json);

  /// Added sugars in g.
  @JsonKey(name: 'added_sugars_g')
  final num? addedSugarsG;

  /// Total carbohydrate in g.
  @JsonKey(name: 'carbs_g')
  final num? carbsG;

  /// Energy in kcal.
  @JsonKey(name: 'energy_kcal')
  final num? energyKcal;

  /// Total fat in g.
  @JsonKey(name: 'fat_g')
  final num? fatG;

  /// Dietary fibre in g.
  @JsonKey(name: 'fiber_g')
  final num? fiberG;

  /// Protein in g.
  @JsonKey(name: 'protein_g')
  final num? proteinG;

  /// Salt in g.
  @JsonKey(name: 'salt_g')
  final num? saltG;

  /// Saturated fat in g.
  @JsonKey(name: 'sat_fat_g')
  final num? satFatG;

  /// Sodium as the number printed, in the unit given by `ProductCreate.sodium_unit` (mg when that is null; the server converts g to mg).
  @JsonKey(name: 'sodium_mg')
  final num? sodiumMg;

  /// Total sugars in g.
  @JsonKey(name: 'sugars_g')
  final num? sugarsG;

  /// Trans fat in g.
  @JsonKey(name: 'trans_fat_g')
  final num? transFatG;

  Map<String, Object?> toJson() => _$PrintedNutrientsToJson(this);
}
