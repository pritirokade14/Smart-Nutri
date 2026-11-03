// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'nutrient_band.dart';

part 'nutrient_bands.g.dart';

/// day: total vs the daily limit; week: vs limit x 7. ``protein_g`` is a target and never.
/// ``over`` (met -> ``ok``). ``unknown`` when the limit is unknown (``kcal`` always), when.
/// nothing was logged, or when the total is incomplete and not already over (protein: not.
/// already met).
@JsonSerializable()
class NutrientBands {
  const NutrientBands({
    required this.kcal,
    required this.proteinG,
    required this.saltG,
    required this.sugarG,
  });

  factory NutrientBands.fromJson(Map<String, Object?> json) =>
      _$NutrientBandsFromJson(json);

  final NutrientBand kcal;
  @JsonKey(name: 'protein_g')
  final NutrientBand proteinG;
  @JsonKey(name: 'salt_g')
  final NutrientBand saltG;
  @JsonKey(name: 'sugar_g')
  final NutrientBand sugarG;

  Map<String, Object?> toJson() => _$NutrientBandsToJson(this);
}
