// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'custom_foods_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CustomFoodsOut _$CustomFoodsOutFromJson(Map<String, dynamic> json) =>
    CustomFoodsOut(
      items: (json['items'] as List<dynamic>)
          .map((e) => CustomFoodOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      nextCursor: json['next_cursor'] as String?,
    );

Map<String, dynamic> _$CustomFoodsOutToJson(CustomFoodsOut instance) =>
    <String, dynamic>{
      'items': instance.items,
      'next_cursor': instance.nextCursor,
    };
