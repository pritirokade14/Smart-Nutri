// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_types_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserTypesOut _$UserTypesOutFromJson(Map<String, dynamic> json) => UserTypesOut(
  activeType: UserTypesOutActiveType.fromJson(json['active_type'] as String),
  answered: json['answered'] as bool,
  answeredAt: json['answered_at'] == null
      ? null
      : DateTime.parse(json['answered_at'] as String),
  followUps: FollowUps.fromJson(json['follow_ups'] as Map<String, dynamic>),
  prefill: json['prefill'] == null
      ? null
      : PrefillSuggestion.fromJson(json['prefill'] as Map<String, dynamic>),
  types: (json['types'] as List<dynamic>)
      .map((e) => UserTypesOutTypes.fromJson(e as String))
      .toList(),
);

Map<String, dynamic> _$UserTypesOutToJson(
  UserTypesOut instance,
) => <String, dynamic>{
  'active_type': _$UserTypesOutActiveTypeEnumMap[instance.activeType]!,
  'answered': instance.answered,
  'answered_at': instance.answeredAt?.toIso8601String(),
  'follow_ups': instance.followUps,
  'prefill': instance.prefill,
  'types': instance.types.map((e) => _$UserTypesOutTypesEnumMap[e]!).toList(),
};

const _$UserTypesOutActiveTypeEnumMap = {
  UserTypesOutActiveType.healthCondition: 'health_condition',
  UserTypesOutActiveType.family: 'family',
  UserTypesOutActiveType.weightLoss: 'weight_loss',
  UserTypesOutActiveType.gym: 'gym',
  UserTypesOutActiveType.allergyDiet: 'allergy_diet',
  UserTypesOutActiveType.eatBetter: 'eat_better',
  UserTypesOutActiveType.$unknown: r'$unknown',
};

const _$UserTypesOutTypesEnumMap = {
  UserTypesOutTypes.healthCondition: 'health_condition',
  UserTypesOutTypes.family: 'family',
  UserTypesOutTypes.weightLoss: 'weight_loss',
  UserTypesOutTypes.gym: 'gym',
  UserTypesOutTypes.allergyDiet: 'allergy_diet',
  UserTypesOutTypes.eatBetter: 'eat_better',
  UserTypesOutTypes.$unknown: r'$unknown',
};
