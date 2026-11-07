// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slots_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotsOut _$MealSlotsOutFromJson(Map<String, dynamic> json) => MealSlotsOut(
  items: (json['items'] as List<dynamic>)
      .map((e) => MealSlotOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  suggestedSlotId: json['suggested_slot_id'] as String,
);

Map<String, dynamic> _$MealSlotsOutToJson(MealSlotsOut instance) =>
    <String, dynamic>{
      'items': instance.items,
      'suggested_slot_id': instance.suggestedSlotId,
    };
