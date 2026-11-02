// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'nutrients_out.dart';
import 'product_out_source.dart';

part 'product_out.g.dart';

@JsonSerializable()
class ProductOut {
  const ProductOut({
    required this.attribution,
    required this.barcode,
    required this.brand,
    required this.category,
    required this.claims,
    required this.imageUrl,
    required this.ingredients,
    required this.name,
    required this.per100g,
    required this.productId,
    required this.servingSizeG,
    required this.source,
  });

  factory ProductOut.fromJson(Map<String, Object?> json) =>
      _$ProductOutFromJson(json);

  final String? attribution;
  final String? barcode;
  final String? brand;
  final String category;
  final List<String> claims;
  @JsonKey(name: 'image_url')
  final String? imageUrl;
  final List<String> ingredients;
  final String? name;
  @JsonKey(name: 'per_100g')
  final NutrientsOut per100g;
  @JsonKey(name: 'product_id')
  final String? productId;
  @JsonKey(name: 'serving_size_g')
  final num? servingSizeG;
  final ProductOutSource source;

  Map<String, Object?> toJson() => _$ProductOutToJson(this);
}
