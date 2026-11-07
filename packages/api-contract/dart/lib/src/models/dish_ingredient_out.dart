// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'dish_ingredient_out.g.dart';

@JsonSerializable()
class DishIngredientOut {
  const DishIngredientOut({required this.grams, required this.name});

  factory DishIngredientOut.fromJson(Map<String, Object?> json) =>
      _$DishIngredientOutFromJson(json);

  final num? grams;
  final String? name;

  Map<String, Object?> toJson() => _$DishIngredientOutToJson(this);
}
