// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'favourite_item_out.dart';
import 'favourite_out_kind.dart';
import 'favourite_out_source_kind.dart';

part 'favourite_out.g.dart';

@JsonSerializable()
class FavouriteOut {
  const FavouriteOut({
    required this.barcode,
    required this.createdAt,
    required this.customFoodId,
    required this.defaultQuantity,
    required this.defaultUnit,
    required this.foodId,
    required this.id,
    required this.itemCount,
    required this.items,
    required this.kind,
    required this.memberId,
    required this.name,
    required this.productId,
    required this.recipeId,
    required this.sourceKind,
    this.attributions,
  });

  factory FavouriteOut.fromJson(Map<String, Object?> json) =>
      _$FavouriteOutFromJson(json);

  final List<String>? attributions;
  final String? barcode;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'custom_food_id')
  final String? customFoodId;
  @JsonKey(name: 'default_quantity')
  final num? defaultQuantity;
  @JsonKey(name: 'default_unit')
  final String? defaultUnit;
  @JsonKey(name: 'food_id')
  final String? foodId;
  final String id;

  /// 1 for a food, the number of saved entries for a meal
  @JsonKey(name: 'item_count')
  final int itemCount;

  /// The saved entries of a meal as they were; null for a food
  final List<FavouriteItemOut>? items;
  final FavouriteOutKind kind;
  @JsonKey(name: 'member_id')
  final String memberId;

  /// A food: its name when starred. A meal: the name you typed (user text)
  final String name;
  @JsonKey(name: 'product_id')
  final String? productId;
  @JsonKey(name: 'recipe_id')
  final String? recipeId;

  /// Null for a saved meal
  @JsonKey(name: 'source_kind')
  final FavouriteOutSourceKind? sourceKind;

  Map<String, Object?> toJson() => _$FavouriteOutToJson(this);
}
