// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'food_hit.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FoodHit _$FoodHitFromJson(Map<String, dynamic> json) => FoodHit(
  attribution: json['attribution'] as String?,
  attributions: (json['attributions'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  brand: json['brand'] as String?,
  grade: json['grade'] == null
      ? null
      : NutriScoreGrade.fromJson(json['grade'] as String),
  group: FoodHitGroup.fromJson(json['group'] as String),
  id: json['id'] as String,
  isDish: json['is_dish'] as bool,
  kind: FoodHitKind.fromJson(json['kind'] as String),
  name: json['name'] as String,
);

Map<String, dynamic> _$FoodHitToJson(FoodHit instance) => <String, dynamic>{
  'attribution': instance.attribution,
  'attributions': instance.attributions,
  'brand': instance.brand,
  'grade': _$NutriScoreGradeEnumMap[instance.grade],
  'group': _$FoodHitGroupEnumMap[instance.group]!,
  'id': instance.id,
  'is_dish': instance.isDish,
  'kind': _$FoodHitKindEnumMap[instance.kind]!,
  'name': instance.name,
};

const _$NutriScoreGradeEnumMap = {
  NutriScoreGrade.a: 'A',
  NutriScoreGrade.b: 'B',
  NutriScoreGrade.c: 'C',
  NutriScoreGrade.d: 'D',
  NutriScoreGrade.e: 'E',
  NutriScoreGrade.$unknown: r'$unknown',
};

const _$FoodHitGroupEnumMap = {
  FoodHitGroup.mine: 'mine',
  FoodHitGroup.indian: 'indian',
  FoodHitGroup.packaged: 'packaged',
  FoodHitGroup.$unknown: r'$unknown',
};

const _$FoodHitKindEnumMap = {
  FoodHitKind.food: 'food',
  FoodHitKind.product: 'product',
  FoodHitKind.off: 'off',
  FoodHitKind.customFood: 'custom_food',
  FoodHitKind.recipe: 'recipe',
  FoodHitKind.$unknown: r'$unknown',
};
