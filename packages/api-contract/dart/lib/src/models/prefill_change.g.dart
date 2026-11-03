// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'prefill_change.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PrefillChange _$PrefillChangeFromJson(Map<String, dynamic> json) =>
    PrefillChange(
      added: (json['added'] as List<dynamic>).map((e) => e as String).toList(),
      current: json['current'],
      field: PrefillChangeField.fromJson(json['field'] as String),
      reason: PrefillChangeReason.fromJson(json['reason'] as String),
      value: json['value'],
    );

Map<String, dynamic> _$PrefillChangeToJson(PrefillChange instance) =>
    <String, dynamic>{
      'added': instance.added,
      'current': instance.current,
      'field': _$PrefillChangeFieldEnumMap[instance.field]!,
      'reason': _$PrefillChangeReasonEnumMap[instance.reason]!,
      'value': instance.value,
    };

const _$PrefillChangeFieldEnumMap = {
  PrefillChangeField.conditions: 'conditions',
  PrefillChangeField.allergens: 'allergens',
  PrefillChangeField.diet: 'diet',
  PrefillChangeField.goal: 'goal',
  PrefillChangeField.customAlerts: 'custom_alerts',
  PrefillChangeField.$unknown: r'$unknown',
};

const _$PrefillChangeReasonEnumMap = {
  PrefillChangeReason.healthCondition: 'health_condition',
  PrefillChangeReason.family: 'family',
  PrefillChangeReason.weightLoss: 'weight_loss',
  PrefillChangeReason.gym: 'gym',
  PrefillChangeReason.allergyDiet: 'allergy_diet',
  PrefillChangeReason.eatBetter: 'eat_better',
  PrefillChangeReason.$unknown: r'$unknown',
};
