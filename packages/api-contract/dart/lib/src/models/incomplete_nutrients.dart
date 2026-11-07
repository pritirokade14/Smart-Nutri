// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'incomplete_nutrients.g.dart';

/// Per nutrient (Totals keys): true when a meal had no value for it. The total then counts.
/// only the known meals and is a lower bound.
@JsonSerializable()
class IncompleteNutrients {
  const IncompleteNutrients({
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.fibreG,
    required this.proteinG,
    required this.saltG,
    required this.sugarsG,
  });

  factory IncompleteNutrients.fromJson(Map<String, Object?> json) =>
      _$IncompleteNutrientsFromJson(json);

  @JsonKey(name: 'carbs_g')
  final bool carbsG;
  @JsonKey(name: 'energy_kcal')
  final bool energyKcal;
  @JsonKey(name: 'fat_g')
  final bool fatG;
  @JsonKey(name: 'fibre_g')
  final bool fibreG;
  @JsonKey(name: 'protein_g')
  final bool proteinG;
  @JsonKey(name: 'salt_g')
  final bool saltG;
  @JsonKey(name: 'sugars_g')
  final bool sugarsG;

  Map<String, Object?> toJson() => _$IncompleteNutrientsToJson(this);
}
