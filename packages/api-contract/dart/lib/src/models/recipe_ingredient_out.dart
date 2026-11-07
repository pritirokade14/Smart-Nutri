// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'recipe_ingredient_out_source_kind.dart';

part 'recipe_ingredient_out.g.dart';

@JsonSerializable()
class RecipeIngredientOut {
  const RecipeIngredientOut({
    required this.attribution,
    required this.available,
    required this.barcode,
    required this.customFoodId,
    required this.foodId,
    required this.grams,
    required this.name,
    required this.position,
    required this.productId,
    required this.quantity,
    required this.sourceKind,
    required this.unit,
  });

  factory RecipeIngredientOut.fromJson(Map<String, Object?> json) =>
      _$RecipeIngredientOutFromJson(json);

  final String? attribution;

  /// false when the custom food it used was deleted: replace it before saving the recipe
  final bool available;
  final String? barcode;
  @JsonKey(name: 'custom_food_id')
  final String? customFoodId;
  @JsonKey(name: 'food_id')
  final String? foodId;

  /// The amount in the ingredient's basis (g, or ml)
  final num grams;
  final String name;
  final int position;
  @JsonKey(name: 'product_id')
  final String? productId;
  final num quantity;
  @JsonKey(name: 'source_kind')
  final RecipeIngredientOutSourceKind sourceKind;
  final String unit;

  Map<String, Object?> toJson() => _$RecipeIngredientOutToJson(this);
}
