// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'dish_out.dart';
import 'food_detail_out_basis.dart';
import 'food_detail_out_kind.dart';
import 'food_unit_out.dart';
import 'numbers_hidden.dart';
import 'nutrient_snapshot.dart';

part 'food_detail_out.g.dart';

@JsonSerializable()
class FoodDetailOut {
  const FoodDetailOut({
    required this.attribution,
    required this.attributions,
    required this.basis,
    required this.brand,
    required this.defaultUnit,
    required this.dish,
    required this.id,
    required this.kind,
    required this.licence,
    required this.name,
    required this.numbersHidden,
    required this.per100,
    required this.reviewPending,
    required this.servingG,
    required this.settableUnits,
    required this.units,
  });

  factory FoodDetailOut.fromJson(Map<String, Object?> json) =>
      _$FoodDetailOutFromJson(json);

  final String? attribution;
  final List<String> attributions;
  final FoodDetailOutBasis basis;
  final String? brand;
  @JsonKey(name: 'default_unit')
  final String defaultUnit;
  final DishOut? dish;
  final String id;
  final FoodDetailOutKind kind;
  final String? licence;
  final String name;
  @JsonKey(name: 'numbers_hidden')
  final NumbersHidden numbersHidden;

  /// Per 100 g (or 100 ml), unrounded; null = unknown, or hidden by the member's numbers display
  @JsonKey(name: 'per_100')
  final NutrientSnapshot per100;

  /// Household measures and dishes are pending dietitian review
  @JsonKey(name: 'review_pending')
  final bool reviewPending;
  @JsonKey(name: 'serving_g')
  final num? servingG;

  /// Units that do not resolve yet and may be given the user's own grams
  @JsonKey(name: 'settable_units')
  final List<String> settableUnits;
  final List<FoodUnitOut> units;

  Map<String, Object?> toJson() => _$FoodDetailOutToJson(this);
}
