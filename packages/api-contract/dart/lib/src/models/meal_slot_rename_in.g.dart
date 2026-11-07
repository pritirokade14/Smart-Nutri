// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slot_rename_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotRenameIn _$MealSlotRenameInFromJson(Map<String, dynamic> json) =>
    MealSlotRenameIn(
      customLabel: json['custom_label'] as String?,
      defaultTimeWindow: json['default_time_window'] == null
          ? null
          : TimeWindow.fromJson(
              json['default_time_window'] as Map<String, dynamic>,
            ),
      clearCustomLabel: json['clear_custom_label'] as bool? ?? false,
      clearTimeWindow: json['clear_time_window'] as bool? ?? false,
    );

Map<String, dynamic> _$MealSlotRenameInToJson(MealSlotRenameIn instance) =>
    <String, dynamic>{
      'clear_custom_label': instance.clearCustomLabel,
      'clear_time_window': instance.clearTimeWindow,
      'custom_label': instance.customLabel,
      'default_time_window': instance.defaultTimeWindow,
    };
