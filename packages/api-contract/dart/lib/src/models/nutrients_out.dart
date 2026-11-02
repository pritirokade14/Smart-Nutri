// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'nutrients_out.g.dart';

@JsonSerializable()
class NutrientsOut {
  const NutrientsOut({
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.fiberG,
    required this.proteinG,
    required this.saltG,
    required this.satFatG,
    required this.sodiumMg,
    required this.sugarsG,
  });

  factory NutrientsOut.fromJson(Map<String, Object?> json) =>
      _$NutrientsOutFromJson(json);

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

  Map<String, Object?> toJson() => _$NutrientsOutToJson(this);
}
