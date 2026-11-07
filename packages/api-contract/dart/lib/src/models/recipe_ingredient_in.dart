// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'recipe_ingredient_in_unit.dart';

part 'recipe_ingredient_in.g.dart';

/// Exactly one reference (a generic food, one of your custom foods, one of our products or.
/// an Open Food Facts barcode), else 422 `invalid_product_ref`, and an amount: ``quantity`` of a.
/// household ``unit`` (grams always work).
@JsonSerializable()
class RecipeIngredientIn {
  const RecipeIngredientIn({
    required this.quantity,
    required this.unit,
    this.barcode,
    this.customFoodId,
    this.foodId,
    this.productId,
  });

  factory RecipeIngredientIn.fromJson(Map<String, Object?> json) =>
      _$RecipeIngredientInFromJson(json);

  final String? barcode;
  @JsonKey(name: 'custom_food_id')
  final String? customFoodId;
  @JsonKey(name: 'food_id')
  final String? foodId;
  @JsonKey(name: 'product_id')
  final String? productId;
  final num quantity;
  final RecipeIngredientInUnit unit;

  Map<String, Object?> toJson() => _$RecipeIngredientInToJson(this);
}
