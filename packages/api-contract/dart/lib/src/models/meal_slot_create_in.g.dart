// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slot_create_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotCreateIn _$MealSlotCreateInFromJson(Map<String, dynamic> json) =>
    MealSlotCreateIn(
      customLabel: json['custom_label'] as String,
      clientId: json['client_id'] as String?,
      defaultTimeWindow: json['default_time_window'] == null
          ? null
          : TimeWindow.fromJson(
              json['default_time_window'] as Map<String, dynamic>,
            ),
      memberId: json['member_id'] as String?,
    );

Map<String, dynamic> _$MealSlotCreateInToJson(MealSlotCreateIn instance) =>
    <String, dynamic>{
      'client_id': instance.clientId,
      'custom_label': instance.customLabel,
      'default_time_window': instance.defaultTimeWindow,
      'member_id': instance.memberId,
    };
