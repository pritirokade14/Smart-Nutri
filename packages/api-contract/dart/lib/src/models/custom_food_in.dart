// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'custom_food_in_basis.dart';
import 'custom_food_in_values_per.dart';
import 'custom_nutrients_in.dart';
import 'custom_portion_in.dart';

part 'custom_food_in.g.dart';

/// A full description of the food (`PUT` replaces it, so a nutrient left out is unknown).
/// ``values_per = "serving"`` needs ``serving_g`` (in the basis unit, g or ml); the API.
/// converts to per 100 g/ml.
@JsonSerializable()
class CustomFoodIn {
  const CustomFoodIn({
    required this.basis,
    required this.name,
    required this.nutrients,
    required this.valuesPer,
    this.barcode,
    this.brand,
    this.clientId,
    this.densityGPerMl,
    this.portions,
    this.servingG,
  });

  factory CustomFoodIn.fromJson(Map<String, Object?> json) =>
      _$CustomFoodInFromJson(json);

  final String? barcode;
  final CustomFoodInBasis basis;
  final String? brand;
  @JsonKey(name: 'client_id')
  final String? clientId;

  /// Grams in one ml
  @JsonKey(name: 'density_g_per_ml')
  final num? densityGPerMl;
  final String name;
  final CustomNutrientsIn nutrients;
  final List<CustomPortionIn>? portions;

  /// Basis units per serving
  @JsonKey(name: 'serving_g')
  final num? servingG;
  @JsonKey(name: 'values_per')
  final CustomFoodInValuesPer valuesPer;

  Map<String, Object?> toJson() => _$CustomFoodInToJson(this);
}
