// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourite_log_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouriteLogOut _$FavouriteLogOutFromJson(Map<String, dynamic> json) =>
    FavouriteLogOut(
      created: (json['created'] as List<dynamic>)
          .map((e) => MealOut.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$FavouriteLogOutToJson(FavouriteLogOut instance) =>
    <String, dynamic>{'created': instance.created};
