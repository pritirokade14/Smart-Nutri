// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'numbers_hidden.dart';
import 'nutrient_snapshot.dart';
import 'recipe_ingredient_out.dart';

part 'recipe_out.g.dart';

@JsonSerializable()
class RecipeOut {
  const RecipeOut({
    required this.attributions,
    required this.basisWeightG,
    required this.cookedWeightG,
    required this.id,
    required this.incompleteNutrients,
    required this.ingredients,
    required this.name,
    required this.numbersHidden,
    required this.per100g,
    required this.perServing,
    required this.servings,
    required this.totalRawG,
    required this.updatedAt,
  });

  factory RecipeOut.fromJson(Map<String, Object?> json) =>
      _$RecipeOutFromJson(json);

  final List<String> attributions;

  /// The cooked weight, or else the raw total
  @JsonKey(name: 'basis_weight_g')
  final num basisWeightG;
  @JsonKey(name: 'cooked_weight_g')
  final num? cookedWeightG;
  final String id;

  /// NutrientSnapshot keys at least one ingredient does not know
  @JsonKey(name: 'incomplete_nutrients')
  final List<String> incompleteNutrients;
  final List<RecipeIngredientOut> ingredients;
  final String name;
  @JsonKey(name: 'numbers_hidden')
  final NumbersHidden numbersHidden;

  /// Per 100 g of the basis weight, 1 dp: the sum of the KNOWN ingredients. A nutrient listed in `incomplete_nutrients` is a lower bound (show it as 'at least'); null when no ingredient knows it, or hidden
  @JsonKey(name: 'per_100g')
  final NutrientSnapshot per100g;

  /// Per serving, 1 dp, same rules; null without `servings`
  @JsonKey(name: 'per_serving')
  final NutrientSnapshot? perServing;
  final num? servings;

  /// The raw total; null when an ingredient has no mass
  @JsonKey(name: 'total_raw_g')
  final num? totalRawG;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Map<String, Object?> toJson() => _$RecipeOutToJson(this);
}
