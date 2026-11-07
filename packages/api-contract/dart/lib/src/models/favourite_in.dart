// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'favourite_in_default_unit.dart';

part 'favourite_in.g.dart';

/// Star a food. Exactly one reference: ``product_id``, ``barcode`` (Open Food Facts or.
/// your own product), ``food_id``, ``custom_food_id`` or ``recipe_id``. ``default_quantity``.
/// with ``default_unit`` is the portion one tap logs; both or neither. A unit that cannot be.
/// converted for this food is 422 ``unit_grams_unknown``.
@JsonSerializable()
class FavouriteIn {
  const FavouriteIn({
    this.barcode,
    this.customFoodId,
    this.defaultQuantity,
    this.defaultUnit,
    this.foodId,
    this.memberId,
    this.productId,
    this.recipeId,
  });

  factory FavouriteIn.fromJson(Map<String, Object?> json) =>
      _$FavouriteInFromJson(json);

  final String? barcode;
  @JsonKey(name: 'custom_food_id')
  final String? customFoodId;
  @JsonKey(name: 'default_quantity')
  final num? defaultQuantity;
  @JsonKey(name: 'default_unit')
  final FavouriteInDefaultUnit? defaultUnit;
  @JsonKey(name: 'food_id')
  final String? foodId;
  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'product_id')
  final String? productId;
  @JsonKey(name: 'recipe_id')
  final String? recipeId;

  Map<String, Object?> toJson() => _$FavouriteInToJson(this);
}
