// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favourites_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavouritesOut _$FavouritesOutFromJson(Map<String, dynamic> json) =>
    FavouritesOut(
      items: (json['items'] as List<dynamic>)
          .map((e) => FavouriteOut.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$FavouritesOutToJson(FavouritesOut instance) =>
    <String, dynamic>{'items': instance.items};
