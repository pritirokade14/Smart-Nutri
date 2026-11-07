// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipes_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipesOut _$RecipesOutFromJson(Map<String, dynamic> json) => RecipesOut(
  items: (json['items'] as List<dynamic>)
      .map((e) => RecipeSummaryOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  nextCursor: json['next_cursor'] as String?,
);

Map<String, dynamic> _$RecipesOutToJson(RecipesOut instance) =>
    <String, dynamic>{
      'items': instance.items,
      'next_cursor': instance.nextCursor,
    };
