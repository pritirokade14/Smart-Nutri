// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_item_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteItemOut _$FavouriteItemOutFromJson(Map<String, dynamic> json) =>
    FavouriteItemOut(
      grams: json['grams'] as num?,
      name: json['name'] as String?,
      quantity: json['quantity'] as num?,
      sourceKind: FavouriteItemOutSourceKind.fromJson(
        json['source_kind'] as String,
      ),
      unit: json['unit'] as String?,
      basis: json['basis'] == null
          ? FavouriteItemOutBasis.g
          : FavouriteItemOutBasis.fromJson(json['basis'] as String),
      attributions: (json['attributions'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$FavouriteItemOutToJson(FavouriteItemOut instance) =>
    <String, dynamic>{
      'attributions': instance.attributions,
      'basis': _$FavouriteItemOutBasisEnumMap[instance.basis]!,
      'grams': instance.grams,
      'name': instance.name,
      'quantity': instance.quantity,
      'source_kind': _$FavouriteItemOutSourceKindEnumMap[instance.sourceKind]!,
      'unit': instance.unit,
    };

const _$FavouriteItemOutBasisEnumMap = {
  FavouriteItemOutBasis.g: 'g',
  FavouriteItemOutBasis.ml: 'ml',
  FavouriteItemOutBasis.$unknown: r'$unknown',
};

const _$FavouriteItemOutSourceKindEnumMap = {
  FavouriteItemOutSourceKind.product: 'product',
  FavouriteItemOutSourceKind.off: 'off',
  FavouriteItemOutSourceKind.food: 'food',
  FavouriteItemOutSourceKind.customFood: 'custom_food',
  FavouriteItemOutSourceKind.recipe: 'recipe',
  FavouriteItemOutSourceKind.quickAdd: 'quick_add',
  FavouriteItemOutSourceKind.$unknown: r'$unknown',
};
