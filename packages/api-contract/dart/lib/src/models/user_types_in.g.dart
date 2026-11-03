// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_types_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserTypesIn _$UserTypesInFromJson(Map<String, dynamic> json) => UserTypesIn(
  types: (json['types'] as List<dynamic>)
      .map((e) => UserTypesInTypes.fromJson(e as String))
      .toList(),
  followUps: json['follow_ups'] == null
      ? null
      : FollowUps.fromJson(json['follow_ups'] as Map<String, dynamic>),
);

Map<String, dynamic> _$UserTypesInToJson(
  UserTypesIn instance,
) => <String, dynamic>{
  'follow_ups': instance.followUps,
  'types': instance.types.map((e) => _$UserTypesInTypesEnumMap[e]!).toList(),
};

const _$UserTypesInTypesEnumMap = {
  UserTypesInTypes.healthCondition: 'health_condition',
  UserTypesInTypes.family: 'family',
  UserTypesInTypes.weightLoss: 'weight_loss',
  UserTypesInTypes.gym: 'gym',
  UserTypesInTypes.allergyDiet: 'allergy_diet',
  UserTypesInTypes.eatBetter: 'eat_better',
  UserTypesInTypes.$unknown: r'$unknown',
};
