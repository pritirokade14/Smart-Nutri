// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'favourite_item_out_basis.dart';
import 'favourite_item_out_source_kind.dart';

part 'favourite_item_out.g.dart';

@JsonSerializable()
class FavouriteItemOut {
  const FavouriteItemOut({
    required this.grams,
    required this.name,
    required this.quantity,
    required this.sourceKind,
    required this.unit,
    this.basis = FavouriteItemOutBasis.g,
    this.attributions,
  });

  factory FavouriteItemOut.fromJson(Map<String, Object?> json) =>
      _$FavouriteItemOutFromJson(json);

  final List<String>? attributions;

  /// The unit of `grams`: grams or millilitres (an ml-basis food)
  final FavouriteItemOutBasis basis;
  final num? grams;
  final String? name;
  final num? quantity;
  @JsonKey(name: 'source_kind')
  final FavouriteItemOutSourceKind sourceKind;
  final String? unit;

  Map<String, Object?> toJson() => _$FavouriteItemOutToJson(this);
}
