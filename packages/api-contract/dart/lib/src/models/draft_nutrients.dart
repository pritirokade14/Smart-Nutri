// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'draft_nutrients.g.dart';

/// Per 100 g / 100 ml for the confirm screen. None = not printed (never invented).
///
/// The engine fields are M1's `NutrientsOut`. `added_sugars_g` and `trans_fat_g` are.
/// shown for the user to confirm but are NOT engine inputs (the engine's `Nutrients`.
/// has no such fields), so `ProductCreate.per_100g` (a `NutrientsOut`) drops them on save.
@JsonSerializable()
class DraftNutrients {
  const DraftNutrients({
    required this.addedSugarsG,
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.fiberG,
    required this.proteinG,
    required this.saltG,
    required this.satFatG,
    required this.sodiumMg,
    required this.sugarsG,
    required this.transFatG,
  });

  factory DraftNutrients.fromJson(Map<String, Object?> json) =>
      _$DraftNutrientsFromJson(json);

  @JsonKey(name: 'added_sugars_g')
  final num? addedSugarsG;
  @JsonKey(name: 'carbs_g')
  final num? carbsG;
  @JsonKey(name: 'energy_kcal')
  final num? energyKcal;
  @JsonKey(name: 'fat_g')
  final num? fatG;
  @JsonKey(name: 'fiber_g')
  final num? fiberG;
  @JsonKey(name: 'protein_g')
  final num? proteinG;
  @JsonKey(name: 'salt_g')
  final num? saltG;
  @JsonKey(name: 'sat_fat_g')
  final num? satFatG;
  @JsonKey(name: 'sodium_mg')
  final num? sodiumMg;
  @JsonKey(name: 'sugars_g')
  final num? sugarsG;
  @JsonKey(name: 'trans_fat_g')
  final num? transFatG;

  Map<String, Object?> toJson() => _$DraftNutrientsToJson(this);
}
