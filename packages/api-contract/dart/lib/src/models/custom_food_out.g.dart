// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'custom_food_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CustomFoodOut _$CustomFoodOutFromJson(Map<String, dynamic> json) =>
    CustomFoodOut(
      barcode: json['barcode'] as String?,
      basis: CustomFoodOutBasis.fromJson(json['basis'] as String),
      brand: json['brand'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      densityGPerMl: json['density_g_per_ml'] as num?,
      entered: EnteredOut.fromJson(json['entered'] as Map<String, dynamic>),
      id: json['id'] as String,
      name: json['name'] as String,
      per100: NutrientSnapshot.fromJson(
        json['per_100'] as Map<String, dynamic>,
      ),
      portions: (json['portions'] as List<dynamic>)
          .map((e) => CustomPortionOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      servingG: json['serving_g'] as num?,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );

Map<String, dynamic> _$CustomFoodOutToJson(CustomFoodOut instance) =>
    <String, dynamic>{
      'barcode': instance.barcode,
      'basis': _$CustomFoodOutBasisEnumMap[instance.basis]!,
      'brand': instance.brand,
      'created_at': instance.createdAt.toIso8601String(),
      'density_g_per_ml': instance.densityGPerMl,
      'entered': instance.entered,
      'id': instance.id,
      'name': instance.name,
      'per_100': instance.per100,
      'portions': instance.portions,
      'serving_g': instance.servingG,
      'updated_at': instance.updatedAt.toIso8601String(),
    };

const _$CustomFoodOutBasisEnumMap = {
  CustomFoodOutBasis.g: 'g',
  CustomFoodOutBasis.ml: 'ml',
  CustomFoodOutBasis.$unknown: r'$unknown',
};
