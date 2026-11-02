// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'product_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProductOut _$ProductOutFromJson(Map<String, dynamic> json) => ProductOut(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  brand: json['brand'] as String?,
  category: json['category'] as String,
  claims: (json['claims'] as List<dynamic>).map((e) => e as String).toList(),
  imageUrl: json['image_url'] as String?,
  ingredients: (json['ingredients'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  name: json['name'] as String?,
  per100g: NutrientsOut.fromJson(json['per_100g'] as Map<String, dynamic>),
  productId: json['product_id'] as String?,
  servingSizeG: json['serving_size_g'] as num?,
  source: ProductOutSource.fromJson(json['source'] as String),
);

Map<String, dynamic> _$ProductOutToJson(ProductOut instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'barcode': instance.barcode,
      'brand': instance.brand,
      'category': instance.category,
      'claims': instance.claims,
      'image_url': instance.imageUrl,
      'ingredients': instance.ingredients,
      'name': instance.name,
      'per_100g': instance.per100g,
      'product_id': instance.productId,
      'serving_size_g': instance.servingSizeG,
      'source': _$ProductOutSourceEnumMap[instance.source]!,
    };

const _$ProductOutSourceEnumMap = {
  ProductOutSource.smartnutri: 'smartnutri',
  ProductOutSource.openfoodfacts: 'openfoodfacts',
  ProductOutSource.$unknown: r'$unknown',
};
