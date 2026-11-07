// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'dish_ingredient_out.dart';

part 'dish_out.g.dart';

@JsonSerializable()
class DishOut {
  const DishOut({
    required this.cookedWeightG,
    required this.ingredients,
    required this.servings,
  });

  factory DishOut.fromJson(Map<String, Object?> json) =>
      _$DishOutFromJson(json);

  @JsonKey(name: 'cooked_weight_g')
  final num? cookedWeightG;
  final List<DishIngredientOut> ingredients;
  final int? servings;

  Map<String, Object?> toJson() => _$DishOutToJson(this);
}
