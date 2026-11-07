// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slots_list_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotsListOut _$MealSlotsListOutFromJson(Map<String, dynamic> json) =>
    MealSlotsListOut(
      items: (json['items'] as List<dynamic>)
          .map((e) => MealSlotOut.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$MealSlotsListOutToJson(MealSlotsListOut instance) =>
    <String, dynamic>{'items': instance.items};
