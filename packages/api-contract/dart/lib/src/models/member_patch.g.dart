// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_patch.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberPatch _$MemberPatchFromJson(Map<String, dynamic> json) => MemberPatch(
  allergens: (json['allergens'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  birthYear: (json['birth_year'] as num?)?.toInt(),
  conditions: (json['conditions'] as List<dynamic>?)
      ?.map((e) => MemberPatchConditions.fromJson(e as String))
      .toList(),
  customAlerts: (json['custom_alerts'] as List<dynamic>?)
      ?.map((e) => MemberPatchCustomAlerts.fromJson(e as String))
      .toList(),
  diet: json['diet'] == null
      ? null
      : MemberPatchDiet.fromJson(json['diet'] as String),
  goal: json['goal'] == null
      ? null
      : MemberPatchGoal.fromJson(json['goal'] as String),
  heightCm: json['height_cm'] as num?,
  name: json['name'] as String?,
  relation: json['relation'] == null
      ? null
      : MemberPatchRelation.fromJson(json['relation'] as String),
  sex: json['sex'] == null
      ? null
      : MemberPatchSex.fromJson(json['sex'] as String),
  weightKg: json['weight_kg'] as num?,
);

Map<String, dynamic> _$MemberPatchToJson(MemberPatch instance) =>
    <String, dynamic>{
      'allergens': instance.allergens,
      'birth_year': instance.birthYear,
      'conditions': instance.conditions
          ?.map((e) => _$MemberPatchConditionsEnumMap[e]!)
          .toList(),
      'custom_alerts': instance.customAlerts
          ?.map((e) => _$MemberPatchCustomAlertsEnumMap[e]!)
          .toList(),
      'diet': _$MemberPatchDietEnumMap[instance.diet],
      'goal': _$MemberPatchGoalEnumMap[instance.goal],
      'height_cm': instance.heightCm,
      'name': instance.name,
      'relation': _$MemberPatchRelationEnumMap[instance.relation],
      'sex': _$MemberPatchSexEnumMap[instance.sex],
      'weight_kg': instance.weightKg,
    };

const _$MemberPatchConditionsEnumMap = {
  MemberPatchConditions.diabetes: 'diabetes',
  MemberPatchConditions.prediabetes: 'prediabetes',
  MemberPatchConditions.pcos: 'pcos',
  MemberPatchConditions.hypertension: 'hypertension',
  MemberPatchConditions.$unknown: r'$unknown',
};

const _$MemberPatchCustomAlertsEnumMap = {
  MemberPatchCustomAlerts.palmOil: 'palm_oil',
  MemberPatchCustomAlerts.maida: 'maida',
  MemberPatchCustomAlerts.addedSugar: 'added_sugar',
  MemberPatchCustomAlerts.artificialSweetener: 'artificial_sweetener',
  MemberPatchCustomAlerts.msg: 'msg',
  MemberPatchCustomAlerts.$unknown: r'$unknown',
};

const _$MemberPatchDietEnumMap = {
  MemberPatchDiet.veg: 'veg',
  MemberPatchDiet.eggetarian: 'eggetarian',
  MemberPatchDiet.vegan: 'vegan',
  MemberPatchDiet.jain: 'jain',
  MemberPatchDiet.nonVeg: 'non_veg',
  MemberPatchDiet.$unknown: r'$unknown',
};

const _$MemberPatchGoalEnumMap = {
  MemberPatchGoal.healthyEating: 'healthy_eating',
  MemberPatchGoal.weightLoss: 'weight_loss',
  MemberPatchGoal.weightGain: 'weight_gain',
  MemberPatchGoal.$unknown: r'$unknown',
};

const _$MemberPatchRelationEnumMap = {
  MemberPatchRelation.self: 'self',
  MemberPatchRelation.child: 'child',
  MemberPatchRelation.parent: 'parent',
  MemberPatchRelation.spouse: 'spouse',
  MemberPatchRelation.other: 'other',
  MemberPatchRelation.$unknown: r'$unknown',
};

const _$MemberPatchSexEnumMap = {
  MemberPatchSex.female: 'female',
  MemberPatchSex.male: 'male',
  MemberPatchSex.other: 'other',
  MemberPatchSex.$unknown: r'$unknown',
};
