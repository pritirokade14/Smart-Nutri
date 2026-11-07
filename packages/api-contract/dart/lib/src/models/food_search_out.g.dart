// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'food_search_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FoodSearchOut _$FoodSearchOutFromJson(Map<String, dynamic> json) =>
    FoodSearchOut(
      failedSources: (json['failed_sources'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      items: (json['items'] as List<dynamic>)
          .map((e) => FoodHit.fromJson(e as Map<String, dynamic>))
          .toList(),
      partial: json['partial'] as bool,
    );

Map<String, dynamic> _$FoodSearchOutToJson(FoodSearchOut instance) =>
    <String, dynamic>{
      'failed_sources': instance.failedSources,
      'items': instance.items,
      'partial': instance.partial,
    };
