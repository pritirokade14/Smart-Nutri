// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recent_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecentItem _$RecentItemFromJson(Map<String, dynamic> json) => RecentItem(
  attribution: json['attribution'] as String?,
  barcode: json['barcode'] as String?,
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  grams: json['grams'] as num,
  lastEatenAt: DateTime.parse(json['last_eaten_at'] as String),
  mealSlotId: json['meal_slot_id'] as String,
  name: json['name'] as String,
  productId: json['product_id'] as String?,
  sourceKind: RecentItemSourceKind.fromJson(json['source_kind'] as String),
  basis: json['basis'] == null
      ? RecentItemBasis.g
      : RecentItemBasis.fromJson(json['basis'] as String),
  attributions: (json['attributions'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  customFoodId: json['custom_food_id'] as String?,
  favouriteId: json['favourite_id'] as String?,
  foodId: json['food_id'] as String?,
  quantity: json['quantity'] as num?,
  recipeId: json['recipe_id'] as String?,
  unit: json['unit'] as String?,
  unitSource: json['unit_source'] == null
      ? null
      : RecentItemUnitSource.fromJson(json['unit_source'] as String),
);

Map<String, dynamic> _$RecentItemToJson(RecentItem instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'attributions': instance.attributions,
      'barcode': instance.barcode,
      'basis': _$RecentItemBasisEnumMap[instance.basis]!,
      'custom_food_id': instance.customFoodId,
      'favourite_id': instance.favouriteId,
      'food_id': instance.foodId,
      'grade': _$NutriScoreGradeEnumMap[instance.grade],
      'grams': instance.grams,
      'last_eaten_at': instance.lastEatenAt.toIso8601String(),
      'meal_slot_id': instance.mealSlotId,
      'name': instance.name,
      'product_id': instance.productId,
      'quantity': instance.quantity,
      'recipe_id': instance.recipeId,
      'source_kind': _$RecentItemSourceKindEnumMap[instance.sourceKind]!,
      'unit': instance.unit,
      'unit_source': _$RecentItemUnitSourceEnumMap[instance.unitSource],
    };

const _$RecentItemBasisEnumMap = {
  RecentItemBasis.g: 'g',
  RecentItemBasis.ml: 'ml',
  RecentItemBasis.$unknown: r'$unknown',
};

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$RecentItemSourceKindEnumMap = {
  RecentItemSourceKind.product: 'product',
  RecentItemSourceKind.off: 'off',
  RecentItemSourceKind.food: 'food',
  RecentItemSourceKind.customFood: 'custom_food',
  RecentItemSourceKind.recipe: 'recipe',
  RecentItemSourceKind.$unknown: r'$unknown',
};

const _$RecentItemUnitSourceEnumMap = {
  RecentItemUnitSource.grams: 'grams',
  RecentItemUnitSource.portion: 'portion',
  RecentItemUnitSource.density: 'density',
  RecentItemUnitSource.$unknown: r'$unknown',
};
