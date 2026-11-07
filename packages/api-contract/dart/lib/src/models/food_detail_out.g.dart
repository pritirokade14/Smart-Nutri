// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'food_detail_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FoodDetailOut _$FoodDetailOutFromJson(Map<String, dynamic> json) =>
    FoodDetailOut(
      attribution: json['attribution'] as String?,
      attributions: (json['attributions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      basis: FoodDetailOutBasis.fromJson(json['basis'] as String),
      brand: json['brand'] as String?,
      defaultUnit: json['default_unit'] as String,
      dish: json['dish'] == null
          ? null
          : DishOut.fromJson(json['dish'] as Map<String, dynamic>),
      id: json['id'] as String,
      kind: FoodDetailOutKind.fromJson(json['kind'] as String),
      licence: json['licence'] as String?,
      name: json['name'] as String,
      numbersHidden: NumbersHidden.fromJson(
        json['numbers_hidden'] as Map<String, dynamic>,
      ),
      per100: NutrientSnapshot.fromJson(
        json['per_100'] as Map<String, dynamic>,
      ),
      reviewPending: json['review_pending'] as bool,
      servingG: json['serving_g'] as num?,
      settableUnits: (json['settable_units'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      units: (json['units'] as List<dynamic>)
          .map((e) => FoodUnitOut.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$FoodDetailOutToJson(FoodDetailOut instance) =>
    <String, dynamic>{
      'attribution': instance.attribution,
      'attributions': instance.attributions,
      'basis': _$FoodDetailOutBasisEnumMap[instance.basis]!,
      'brand': instance.brand,
      'default_unit': instance.defaultUnit,
      'dish': instance.dish,
      'id': instance.id,
      'kind': _$FoodDetailOutKindEnumMap[instance.kind]!,
      'licence': instance.licence,
      'name': instance.name,
      'numbers_hidden': instance.numbersHidden,
      'per_100': instance.per100,
      'review_pending': instance.reviewPending,
      'serving_g': instance.servingG,
      'settable_units': instance.settableUnits,
      'units': instance.units,
    };

const _$FoodDetailOutBasisEnumMap = {
  FoodDetailOutBasis.g: 'g',
  FoodDetailOutBasis.ml: 'ml',
  FoodDetailOutBasis.$unknown: r'$unknown',
};

const _$FoodDetailOutKindEnumMap = {
  FoodDetailOutKind.food: 'food',
  FoodDetailOutKind.product: 'product',
  FoodDetailOutKind.off: 'off',
  FoodDetailOutKind.$unknown: r'$unknown',
};
