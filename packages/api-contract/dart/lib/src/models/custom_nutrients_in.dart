// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'custom_nutrients_in.g.dart';

/// What the label says, per 100 g/ml or per serving (`values_per`). A blank is `null`.
/// (unknown). Salt and sodium follow the engine's rule (the higher one wins).
@JsonSerializable()
class CustomNutrientsIn {
  const CustomNutrientsIn({
    this.carbsG,
    this.energyKcal,
    this.fatG,
    this.fibreG,
    this.proteinG,
    this.saltG,
    this.satFatG,
    this.sodiumMg,
    this.sugarsG,
  });

  factory CustomNutrientsIn.fromJson(Map<String, Object?> json) =>
      _$CustomNutrientsInFromJson(json);

  @JsonKey(name: 'carbs_g')
  final num? carbsG;
  @JsonKey(name: 'energy_kcal')
  final num? energyKcal;
  @JsonKey(name: 'fat_g')
  final num? fatG;
  @JsonKey(name: 'fibre_g')
  final num? fibreG;
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

  Map<String, Object?> toJson() => _$CustomNutrientsInToJson(this);
}
