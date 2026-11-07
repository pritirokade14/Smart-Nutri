// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_meal_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteMealIn _$FavouriteMealInFromJson(Map<String, dynamic> json) =>
    FavouriteMealIn(
      fromDate: DateTime.parse(json['from_date'] as String),
      fromSlotId: json['from_slot_id'] as String,
      name: json['name'] as String,
      clientId: json['client_id'] as String?,
      memberId: json['member_id'] as String?,
    );

Map<String, dynamic> _$FavouriteMealInToJson(FavouriteMealIn instance) =>
    <String, dynamic>{
      'client_id': instance.clientId,
      'from_date': instance.fromDate.toIso8601String(),
      'from_slot_id': instance.fromSlotId,
      'member_id': instance.memberId,
      'name': instance.name,
    };
