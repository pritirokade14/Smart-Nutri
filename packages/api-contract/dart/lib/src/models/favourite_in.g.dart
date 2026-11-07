// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteIn _$FavouriteInFromJson(Map<String, dynamic> json) => FavouriteIn(
  barcode: json['barcode'] as String?,
  customFoodId: json['custom_food_id'] as String?,
  defaultQuantity: json['default_quantity'] as num?,
  defaultUnit: json['default_unit'] == null
      ? null
      : FavouriteInDefaultUnit.fromJson(json['default_unit'] as String),
  foodId: json['food_id'] as String?,
  memberId: json['member_id'] as String?,
  productId: json['product_id'] as String?,
  recipeId: json['recipe_id'] as String?,
);

Map<String, dynamic> _$FavouriteInToJson(FavouriteIn instance) =>
    <String, dynamic>{
      'barcode': instance.barcode,
      'custom_food_id': instance.customFoodId,
      'default_quantity': instance.defaultQuantity,
      'default_unit': _$FavouriteInDefaultUnitEnumMap[instance.defaultUnit],
      'food_id': instance.foodId,
      'member_id': instance.memberId,
      'product_id': instance.productId,
      'recipe_id': instance.recipeId,
    };

const _$FavouriteInDefaultUnitEnumMap = {
  FavouriteInDefaultUnit.g: 'g',
  FavouriteInDefaultUnit.ml: 'ml',
  FavouriteInDefaultUnit.serving: 'serving',
  FavouriteInDefaultUnit.piece: 'piece',
  FavouriteInDefaultUnit.pieceSmall: 'piece_small',
  FavouriteInDefaultUnit.pieceMedium: 'piece_medium',
  FavouriteInDefaultUnit.pieceLarge: 'piece_large',
  FavouriteInDefaultUnit.roti: 'roti',
  FavouriteInDefaultUnit.slice: 'slice',
  FavouriteInDefaultUnit.katori: 'katori',
  FavouriteInDefaultUnit.katoriSmall: 'katori_small',
  FavouriteInDefaultUnit.katoriMedium: 'katori_medium',
  FavouriteInDefaultUnit.katoriLarge: 'katori_large',
  FavouriteInDefaultUnit.cup: 'cup',
  FavouriteInDefaultUnit.glass: 'glass',
  FavouriteInDefaultUnit.tbsp: 'tbsp',
  FavouriteInDefaultUnit.tsp: 'tsp',
  FavouriteInDefaultUnit.$unknown: r'$unknown',
};
