// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_slots_order_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MealSlotsOrderIn _$MealSlotsOrderInFromJson(Map<String, dynamic> json) =>
    MealSlotsOrderIn(
      ids: (json['ids'] as List<dynamic>).map((e) => e as String).toList(),
      memberId: json['member_id'] as String?,
    );

Map<String, dynamic> _$MealSlotsOrderInToJson(MealSlotsOrderIn instance) =>
    <String, dynamic>{'ids': instance.ids, 'member_id': instance.memberId};
