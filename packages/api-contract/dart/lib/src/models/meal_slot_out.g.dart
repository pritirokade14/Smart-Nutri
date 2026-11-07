// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slot_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotOut _$MealSlotOutFromJson(Map<String, dynamic> json) => MealSlotOut(
  archived: json['archived'] as bool,
  customLabel: json['custom_label'] as String?,
  defaultTimeWindow: json['default_time_window'] == null
      ? null
      : TimeWindow.fromJson(
          json['default_time_window'] as Map<String, dynamic>,
        ),
  id: json['id'] as String,
  isDefault: json['is_default'] as bool,
  labelKey: json['label_key'] as String?,
  memberId: json['member_id'] as String,
  position: (json['position'] as num).toInt(),
);

Map<String, dynamic> _$MealSlotOutToJson(MealSlotOut instance) =>
    <String, dynamic>{
      'archived': instance.archived,
      'custom_label': instance.customLabel,
      'default_time_window': instance.defaultTimeWindow,
      'id': instance.id,
      'is_default': instance.isDefault,
      'label_key': instance.labelKey,
      'member_id': instance.memberId,
      'position': instance.position,
    };
