// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'active_type_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ActiveTypeIn _$ActiveTypeInFromJson(Map<String, dynamic> json) => ActiveTypeIn(
  activeType: ActiveTypeInActiveType.fromJson(json['active_type'] as String),
);

Map<String, dynamic> _$ActiveTypeInToJson(ActiveTypeIn instance) =>
    <String, dynamic>{
      'active_type': _$ActiveTypeInActiveTypeEnumMap[instance.activeType]!,
    };

const _$ActiveTypeInActiveTypeEnumMap = {
  ActiveTypeInActiveType.healthCondition: 'health_condition',
  ActiveTypeInActiveType.family: 'family',
  ActiveTypeInActiveType.weightLoss: 'weight_loss',
  ActiveTypeInActiveType.gym: 'gym',
  ActiveTypeInActiveType.allergyDiet: 'allergy_diet',
  ActiveTypeInActiveType.eatBetter: 'eat_better',
  ActiveTypeInActiveType.$unknown: r'$unknown',
};
