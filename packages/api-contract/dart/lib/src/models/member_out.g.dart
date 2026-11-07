// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberOut _$MemberOutFromJson(Map<String, dynamic> json) => MemberOut(
  allergens: (json['allergens'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  birthYear: (json['birth_year'] as num?)?.toInt(),
  bodyFatPct: json['body_fat_pct'] as num?,
  conditions: (json['conditions'] as List<dynamic>)
      .map((e) => MemberOutConditions.fromJson(e as String))
      .toList(),
  customAlerts: (json['custom_alerts'] as List<dynamic>)
      .map((e) => MemberOutCustomAlerts.fromJson(e as String))
      .toList(),
  diet: MemberOutDiet.fromJson(json['diet'] as String),
  goal: json['goal'] == null
      ? null
      : MemberOutGoal.fromJson(json['goal'] as String),
  heightCm: json['height_cm'] as num?,
  id: json['id'] as String,
  isPrimary: json['is_primary'] as bool,
  name: json['name'] as String,
  relation: MemberOutRelation.fromJson(json['relation'] as String),
  sex: json['sex'] == null
      ? null
      : MemberOutSex.fromJson(json['sex'] as String),
  weightKg: json['weight_kg'] as num?,
);

Map<String, dynamic> _$MemberOutToJson(MemberOut instance) => <String, dynamic>{
  'allergens': instance.allergens,
  'birth_year': instance.birthYear,
  'body_fat_pct': instance.bodyFatPct,
  'conditions': instance.conditions
      .map((e) => _$MemberOutConditionsEnumMap[e]!)
      .toList(),
  'custom_alerts': instance.customAlerts
      .map((e) => _$MemberOutCustomAlertsEnumMap[e]!)
      .toList(),
  'diet': _$MemberOutDietEnumMap[instance.diet]!,
  'goal': _$MemberOutGoalEnumMap[instance.goal],
  'height_cm': instance.heightCm,
  'id': instance.id,
  'is_primary': instance.isPrimary,
  'name': instance.name,
  'relation': _$MemberOutRelationEnumMap[instance.relation]!,
  'sex': _$MemberOutSexEnumMap[instance.sex],
  'weight_kg': instance.weightKg,
};

const _$MemberOutConditionsEnumMap = {
  MemberOutConditions.diabetes: 'diabetes',
  MemberOutConditions.prediabetes: 'prediabetes',
  MemberOutConditions.pcos: 'pcos',
  MemberOutConditions.hypertension: 'hypertension',
  MemberOutConditions.$unknown: r'$unknown',
};

const _$MemberOutCustomAlertsEnumMap = {
  MemberOutCustomAlerts.palmOil: 'palm_oil',
  MemberOutCustomAlerts.maida: 'maida',
  MemberOutCustomAlerts.addedSugar: 'added_sugar',
  MemberOutCustomAlerts.artificialSweetener: 'artificial_sweetener',
  MemberOutCustomAlerts.msg: 'msg',
  MemberOutCustomAlerts.$unknown: r'$unknown',
};

const _$MemberOutDietEnumMap = {
  MemberOutDiet.veg: 'veg',
  MemberOutDiet.eggetarian: 'eggetarian',
  MemberOutDiet.vegan: 'vegan',
  MemberOutDiet.jain: 'jain',
  MemberOutDiet.nonVeg: 'non_veg',
  MemberOutDiet.$unknown: r'$unknown',
};

const _$MemberOutGoalEnumMap = {
  MemberOutGoal.healthyEating: 'healthy_eating',
  MemberOutGoal.weightLoss: 'weight_loss',
  MemberOutGoal.weightGain: 'weight_gain',
  MemberOutGoal.buildMuscle: 'build_muscle',
  MemberOutGoal.$unknown: r'$unknown',
};

const _$MemberOutRelationEnumMap = {
  MemberOutRelation.self: 'self',
  MemberOutRelation.child: 'child',
  MemberOutRelation.parent: 'parent',
  MemberOutRelation.spouse: 'spouse',
  MemberOutRelation.other: 'other',
  MemberOutRelation.$unknown: r'$unknown',
};

const _$MemberOutSexEnumMap = {
  MemberOutSex.female: 'female',
  MemberOutSex.male: 'male',
  MemberOutSex.other: 'other',
  MemberOutSex.$unknown: r'$unknown',
};
