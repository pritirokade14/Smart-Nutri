// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'custom_food_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CustomFoodIn _$CustomFoodInFromJson(Map<String, dynamic> json) => CustomFoodIn(
  basis: CustomFoodInBasis.fromJson(json['basis'] as String),
  name: json['name'] as String,
  nutrients: CustomNutrientsIn.fromJson(
    json['nutrients'] as Map<String, dynamic>,
  ),
  valuesPer: CustomFoodInValuesPer.fromJson(json['values_per'] as String),
  barcode: json['barcode'] as String?,
  brand: json['brand'] as String?,
  clientId: json['client_id'] as String?,
  densityGPerMl: json['density_g_per_ml'] as num?,
  portions: (json['portions'] as List<dynamic>?)
      ?.map((e) => CustomPortionIn.fromJson(e as Map<String, dynamic>))
      .toList(),
  servingG: json['serving_g'] as num?,
);

Map<String, dynamic> _$CustomFoodInToJson(CustomFoodIn instance) =>
    <String, dynamic>{
      'barcode': instance.barcode,
      'basis': _$CustomFoodInBasisEnumMap[instance.basis]!,
      'brand': instance.brand,
      'client_id': instance.clientId,
      'density_g_per_ml': instance.densityGPerMl,
      'name': instance.name,
      'nutrients': instance.nutrients,
      'portions': instance.portions,
      'serving_g': instance.servingG,
      'values_per': _$CustomFoodInValuesPerEnumMap[instance.valuesPer]!,
    };

const _$CustomFoodInBasisEnumMap = {
  CustomFoodInBasis.g: 'g',
  CustomFoodInBasis.ml: 'ml',
  CustomFoodInBasis.$unknown: r'$unknown',
};

const _$CustomFoodInValuesPerEnumMap = {
  CustomFoodInValuesPer.value100: '100',
  CustomFoodInValuesPer.serving: 'serving',
  CustomFoodInValuesPer.$unknown: r'$unknown',
};
