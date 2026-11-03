// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'product_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProductCreate _$ProductCreateFromJson(Map<String, dynamic> json) =>
    ProductCreate(
      name: json['name'] as String,
      per100g: NutrientsOut.fromJson(json['per_100g'] as Map<String, dynamic>),
      category: json['category'] == null
          ? ProductCreateCategory.general
          : ProductCreateCategory.fromJson(json['category'] as String),
      claims:
          (json['claims'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      confirmedFields:
          (json['confirmed_fields'] as List<dynamic>?)
              ?.map((e) => ProductCreateConfirmedFields.fromJson(e as String))
              .toList() ??
          const [],
      ingredients:
          (json['ingredients'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      allergenStatement: json['allergen_statement'] as String?,
      barcode: json['barcode'] as String?,
      brand: json['brand'] as String?,
      mayContainStatement: json['may_contain_statement'] as String?,
      scanId: json['scan_id'] as String?,
      servingSizeG: json['serving_size_g'] as num?,
      vegMark: json['veg_mark'] == null
          ? null
          : ProductCreateVegMark.fromJson(json['veg_mark'] as String),
    );

Map<String, dynamic> _$ProductCreateToJson(ProductCreate instance) =>
    <String, dynamic>{
      'allergen_statement': instance.allergenStatement,
      'barcode': instance.barcode,
      'brand': instance.brand,
      'category': _$ProductCreateCategoryEnumMap[instance.category]!,
      'claims': instance.claims,
      'confirmed_fields': instance.confirmedFields
          .map((e) => _$ProductCreateConfirmedFieldsEnumMap[e]!)
          .toList(),
      'ingredients': instance.ingredients,
      'may_contain_statement': instance.mayContainStatement,
      'name': instance.name,
      'per_100g': instance.per100g,
      'scan_id': instance.scanId,
      'serving_size_g': instance.servingSizeG,
      'veg_mark': _$ProductCreateVegMarkEnumMap[instance.vegMark],
    };

const _$ProductCreateCategoryEnumMap = {
  ProductCreateCategory.general: 'general',
  ProductCreateCategory.beverage: 'beverage',
  ProductCreateCategory.water: 'water',
  ProductCreateCategory.cheese: 'cheese',
  ProductCreateCategory.fat: 'fat',
  ProductCreateCategory.$unknown: r'$unknown',
};

const _$ProductCreateConfirmedFieldsEnumMap = {
  ProductCreateConfirmedFields.energyKcal: 'energy_kcal',
  ProductCreateConfirmedFields.proteinG: 'protein_g',
  ProductCreateConfirmedFields.carbsG: 'carbs_g',
  ProductCreateConfirmedFields.sugarsG: 'sugars_g',
  ProductCreateConfirmedFields.fatG: 'fat_g',
  ProductCreateConfirmedFields.satFatG: 'sat_fat_g',
  ProductCreateConfirmedFields.fiberG: 'fiber_g',
  ProductCreateConfirmedFields.saltG: 'salt_g',
  ProductCreateConfirmedFields.sodiumMg: 'sodium_mg',
  ProductCreateConfirmedFields.$unknown: r'$unknown',
};

const _$ProductCreateVegMarkEnumMap = {
  ProductCreateVegMark.veg: 'veg',
  ProductCreateVegMark.nonVeg: 'non_veg',
  ProductCreateVegMark.$unknown: r'$unknown',
};
