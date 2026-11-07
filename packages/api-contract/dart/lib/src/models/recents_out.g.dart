// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recents_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecentsOut _$RecentsOutFromJson(Map<String, dynamic> json) => RecentsOut(
  items: (json['items'] as List<dynamic>)
      .map((e) => RecentItem.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$RecentsOutToJson(RecentsOut instance) =>
    <String, dynamic>{'items': instance.items};
