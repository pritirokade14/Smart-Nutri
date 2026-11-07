// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'recipe_ingredient_in.dart';

part 'recipe_in.g.dart';

/// ``servings`` (optional) gives the per-serving values; ``cooked_weight_g`` (optional) is the.
/// pot weighed after cooking, the best basis for the per-100 g values. Without it the raw.
/// total is used, which needs every ingredient to have a mass.
@JsonSerializable()
class RecipeIn {
  const RecipeIn({
    required this.ingredients,
    required this.name,
    this.clientId,
    this.cookedWeightG,
    this.servings,
  });

  factory RecipeIn.fromJson(Map<String, Object?> json) =>
      _$RecipeInFromJson(json);

  @JsonKey(name: 'client_id')
  final String? clientId;
  @JsonKey(name: 'cooked_weight_g')
  final num? cookedWeightG;

  /// 1 to 50, else 422 `recipe_ingredient_limit`
  final List<RecipeIngredientIn> ingredients;
  final String name;
  final num? servings;

  Map<String, Object?> toJson() => _$RecipeInToJson(this);
}
