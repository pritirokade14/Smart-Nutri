// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteOut _$FavouriteOutFromJson(Map<String, dynamic> json) => FavouriteOut(
  barcode: json['barcode'] as String?,
  createdAt: DateTime.parse(json['created_at'] as String),
  customFoodId: json['custom_food_id'] as String?,
  defaultQuantity: json['default_quantity'] as num?,
  defaultUnit: json['default_unit'] as String?,
  foodId: json['food_id'] as String?,
  id: json['id'] as String,
  itemCount: (json['item_count'] as num).toInt(),
  items: (json['items'] as List<dynamic>?)
      ?.map((e) => FavouriteItemOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  kind: FavouriteOutKind.fromJson(json['kind'] as String),
  memberId: json['member_id'] as String,
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  recipeId: json['recipe_id'] as String?,
  sourceKind: json['source_kind'] == null
      ? null
      : FavouriteOutSourceKind.fromJson(json['source_kind'] as String),
  attributions: (json['attributions'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$FavouriteOutToJson(FavouriteOut instance) =>
    <String, dynamic>{
      'attributions': instance.attributions,
      'barcode': instance.barcode,
      'created_at': instance.createdAt.toIso8601String(),
      'custom_food_id': instance.customFoodId,
      'default_quantity': instance.defaultQuantity,
      'default_unit': instance.defaultUnit,
      'food_id': instance.foodId,
      'id': instance.id,
      'item_count': instance.itemCount,
      'items': instance.items,
      'kind': _$FavouriteOutKindEnumMap[instance.kind]!,
      'member_id': instance.memberId,
      'name': instance.name,
      'product_id': instance.productId,
      'recipe_id': instance.recipeId,
      'source_kind': _$FavouriteOutSourceKindEnumMap[instance.sourceKind],
    };

const _$FavouriteOutKindEnumMap = {
  FavouriteOutKind.food: 'food',
  FavouriteOutKind.meal: 'meal',
  FavouriteOutKind.$unknown: r'$unknown',
};

const _$FavouriteOutSourceKindEnumMap = {
  FavouriteOutSourceKind.product: 'product',
  FavouriteOutSourceKind.off: 'off',
  FavouriteOutSourceKind.food: 'food',
  FavouriteOutSourceKind.customFood: 'custom_food',
  FavouriteOutSourceKind.recipe: 'recipe',
  FavouriteOutSourceKind.$unknown: r'$unknown',
};
