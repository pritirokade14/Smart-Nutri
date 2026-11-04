// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'follow_ups.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FollowUps _$FollowUpsFromJson(Map<String, dynamic> json) => FollowUps(
  alerts: (json['alerts'] as List<dynamic>?)
      ?.map((e) => FollowUpsAlerts.fromJson(e as String))
      .toList(),
  allergens: (json['allergens'] as List<dynamic>?)
      ?.map((e) => FollowUpsAllergens.fromJson(e as String))
      .toList(),
  conditions: (json['conditions'] as List<dynamic>?)
      ?.map((e) => FollowUpsConditions.fromJson(e as String))
      .toList(),
  diet: json['diet'] == null
      ? null
      : FollowUpsDiet.fromJson(json['diet'] as String),
  familyWith: (json['family_with'] as List<dynamic>?)
      ?.map((e) => FollowUpsFamilyWith.fromJson(e as String))
      .toList(),
  gymGoal: json['gym_goal'] == null
      ? null
      : FollowUpsGymGoal.fromJson(json['gym_goal'] as String),
);

Map<String, dynamic> _$FollowUpsToJson(FollowUps instance) => <String, dynamic>{
  'alerts': instance.alerts?.map((e) => _$FollowUpsAlertsEnumMap[e]!).toList(),
  'allergens': instance.allergens
      ?.map((e) => _$FollowUpsAllergensEnumMap[e]!)
      .toList(),
  'conditions': instance.conditions
      ?.map((e) => _$FollowUpsConditionsEnumMap[e]!)
      .toList(),
  'diet': _$FollowUpsDietEnumMap[instance.diet],
  'family_with': instance.familyWith
      ?.map((e) => _$FollowUpsFamilyWithEnumMap[e]!)
      .toList(),
  'gym_goal': _$FollowUpsGymGoalEnumMap[instance.gymGoal],
};

const _$FollowUpsAlertsEnumMap = {
  FollowUpsAlerts.palmOil: 'palm_oil',
  FollowUpsAlerts.maida: 'maida',
  FollowUpsAlerts.addedSugar: 'added_sugar',
  FollowUpsAlerts.artificialSweetener: 'artificial_sweetener',
  FollowUpsAlerts.msg: 'msg',
  FollowUpsAlerts.$unknown: r'$unknown',
};

const _$FollowUpsAllergensEnumMap = {
  FollowUpsAllergens.milk: 'milk',
  FollowUpsAllergens.peanut: 'peanut',
  FollowUpsAllergens.gluten: 'gluten',
  FollowUpsAllergens.soy: 'soy',
  FollowUpsAllergens.egg: 'egg',
  FollowUpsAllergens.treeNut: 'tree_nut',
  FollowUpsAllergens.sesame: 'sesame',
  FollowUpsAllergens.fish: 'fish',
  FollowUpsAllergens.crustacean: 'crustacean',
  FollowUpsAllergens.mustard: 'mustard',
  FollowUpsAllergens.sulphite: 'sulphite',
  FollowUpsAllergens.$unknown: r'$unknown',
};

const _$FollowUpsConditionsEnumMap = {
  FollowUpsConditions.diabetes: 'diabetes',
  FollowUpsConditions.prediabetes: 'prediabetes',
  FollowUpsConditions.pcos: 'pcos',
  FollowUpsConditions.hypertension: 'hypertension',
  FollowUpsConditions.$unknown: r'$unknown',
};

const _$FollowUpsDietEnumMap = {
  FollowUpsDiet.veg: 'veg',
  FollowUpsDiet.eggetarian: 'eggetarian',
  FollowUpsDiet.vegan: 'vegan',
  FollowUpsDiet.jain: 'jain',
  FollowUpsDiet.nonVeg: 'non_veg',
  FollowUpsDiet.$unknown: r'$unknown',
};

const _$FollowUpsFamilyWithEnumMap = {
  FollowUpsFamilyWith.children: 'children',
  FollowUpsFamilyWith.parents: 'parents',
  FollowUpsFamilyWith.partner: 'partner',
  FollowUpsFamilyWith.others: 'others',
  FollowUpsFamilyWith.$unknown: r'$unknown',
};

const _$FollowUpsGymGoalEnumMap = {
  FollowUpsGymGoal.buildMuscle: 'build_muscle',
  FollowUpsGymGoal.loseFat: 'lose_fat',
  FollowUpsGymGoal.stayFit: 'stay_fit',
  FollowUpsGymGoal.$unknown: r'$unknown',
};
