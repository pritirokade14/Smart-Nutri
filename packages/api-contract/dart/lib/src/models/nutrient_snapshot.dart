// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'nutrient_snapshot.g.dart';

/// Nutrients in the portion eaten (per_100g x grams / 100, 1 dp). null = not on the label.
/// (never counted as 0).
@JsonSerializable()
class NutrientSnapshot {
  const NutrientSnapshot({
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.fibreG,
    required this.proteinG,
    required this.saltG,
    required this.satFatG,
    required this.sugarsG,
  });

  factory NutrientSnapshot.fromJson(Map<String, Object?> json) =>
      _$NutrientSnapshotFromJson(json);

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
  @JsonKey(name: 'sugars_g')
  final num? sugarsG;

  Map<String, Object?> toJson() => _$NutrientSnapshotToJson(this);
}
