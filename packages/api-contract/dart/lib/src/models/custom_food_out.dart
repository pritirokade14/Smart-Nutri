// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'custom_food_out_basis.dart';
import 'custom_portion_out.dart';
import 'entered_out.dart';
import 'nutrient_snapshot.dart';

part 'custom_food_out.g.dart';

/// Not redacted by the numbers display: it is the label the user typed and needs it to.
/// edit (G15).
@JsonSerializable()
class CustomFoodOut {
  const CustomFoodOut({
    required this.barcode,
    required this.basis,
    required this.brand,
    required this.createdAt,
    required this.densityGPerMl,
    required this.entered,
    required this.id,
    required this.name,
    required this.per100,
    required this.portions,
    required this.servingG,
    required this.updatedAt,
  });

  factory CustomFoodOut.fromJson(Map<String, Object?> json) =>
      _$CustomFoodOutFromJson(json);

  final String? barcode;
  final CustomFoodOutBasis basis;
  final String? brand;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'density_g_per_ml')
  final num? densityGPerMl;

  /// The values as typed
  final EnteredOut entered;
  final String id;
  final String name;

  /// Per 100 g (or 100 ml), unrounded; null = unknown
  @JsonKey(name: 'per_100')
  final NutrientSnapshot per100;
  final List<CustomPortionOut> portions;
  @JsonKey(name: 'serving_g')
  final num? servingG;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$CustomFoodOutToJson(this);
}
