// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberIn _$MemberInFromJson(Map<String, dynamic> json) => MemberIn(
  birthYear: (json['birth_year'] as num).toInt(),
  name: json['name'] as String,
  relation: MemberInRelation.fromJson(json['relation'] as String),
  bodyFatPct: json['body_fat_pct'] as num?,
  goal: json['goal'] == null
      ? null
      : MemberInGoal.fromJson(json['goal'] as String),
  heightCm: json['height_cm'] as num?,
  sex: json['sex'] == null ? null : MemberInSex.fromJson(json['sex'] as String),
  weightKg: json['weight_kg'] as num?,
  allergens:
      (json['allergens'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  conditions:
      (json['conditions'] as List<dynamic>?)
          ?.map((e) => MemberInConditions.fromJson(e as String))
          .toList() ??
      const [],
  customAlerts:
      (json['custom_alerts'] as List<dynamic>?)
          ?.map((e) => MemberInCustomAlerts.fromJson(e as String))
          .toList() ??
      const [],
  diet: json['diet'] == null
      ? MemberInDiet.nonVeg
      : MemberInDiet.fromJson(json['diet'] as String),
);

Map<String, dynamic> _$MemberInToJson(MemberIn instance) => <String, dynamic>{
  'allergens': instance.allergens,
  'birth_year': instance.birthYear,
  'body_fat_pct': instance.bodyFatPct,
  'conditions': instance.conditions
      .map((e) => _$MemberInConditionsEnumMap[e]!)
      .toList(),
  'custom_alerts': instance.customAlerts
      .map((e) => _$MemberInCustomAlertsEnumMap[e]!)
      .toList(),
  'diet': _$MemberInDietEnumMap[instance.diet]!,
  'goal': _$MemberInGoalEnumMap[instance.goal],
  'height_cm': instance.heightCm,
  'name': instance.name,
  'relation': _$MemberInRelationEnumMap[instance.relation]!,
  'sex': _$MemberInSexEnumMap[instance.sex],
  'weight_kg': instance.weightKg,
};

const _$MemberInConditionsEnumMap = {
  MemberInConditions.diabetes: 'diabetes',
  MemberInConditions.prediabetes: 'prediabetes',
  MemberInConditions.pcos: 'pcos',
  MemberInConditions.hypertension: 'hypertension',
  MemberInConditions.$unknown: r'$unknown',
};

const _$MemberInCustomAlertsEnumMap = {
  MemberInCustomAlerts.palmOil: 'palm_oil',
  MemberInCustomAlerts.maida: 'maida',
  MemberInCustomAlerts.addedSugar: 'added_sugar',
  MemberInCustomAlerts.artificialSweetener: 'artificial_sweetener',
  MemberInCustomAlerts.msg: 'msg',
  MemberInCustomAlerts.$unknown: r'$unknown',
};

const _$MemberInDietEnumMap = {
  MemberInDiet.veg: 'veg',
  MemberInDiet.eggetarian: 'eggetarian',
  MemberInDiet.vegan: 'vegan',
  MemberInDiet.jain: 'jain',
  MemberInDiet.nonVeg: 'non_veg',
  MemberInDiet.$unknown: r'$unknown',
};

const _$MemberInGoalEnumMap = {
  MemberInGoal.healthyEating: 'healthy_eating',
  MemberInGoal.weightLoss: 'weight_loss',
  MemberInGoal.weightGain: 'weight_gain',
  MemberInGoal.buildMuscle: 'build_muscle',
  MemberInGoal.$unknown: r'$unknown',
};

const _$MemberInRelationEnumMap = {
  MemberInRelation.child: 'child',
  MemberInRelation.parent: 'parent',
  MemberInRelation.spouse: 'spouse',
  MemberInRelation.other: 'other',
  MemberInRelation.$unknown: r'$unknown',
};

const _$MemberInSexEnumMap = {
  MemberInSex.female: 'female',
  MemberInSex.male: 'male',
  MemberInSex.other: 'other',
  MemberInSex.$unknown: r'$unknown',
};
