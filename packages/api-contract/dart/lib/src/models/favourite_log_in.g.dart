// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_log_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteLogIn _$FavouriteLogInFromJson(Map<String, dynamic> json) =>
    FavouriteLogIn(
      clientId: json['client_id'] as String,
      localDate: json['local_date'] == null
          ? null
          : DateTime.parse(json['local_date'] as String),
      mealSlotId: json['meal_slot_id'] as String?,
    );

Map<String, dynamic> _$FavouriteLogInToJson(FavouriteLogIn instance) =>
    <String, dynamic>{
      'client_id': instance.clientId,
      'local_date': instance.localDate?.toIso8601String(),
      'meal_slot_id': instance.mealSlotId,
    };
