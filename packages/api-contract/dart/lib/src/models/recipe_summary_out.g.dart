// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'recipe_summary_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RecipeSummaryOut _$RecipeSummaryOutFromJson(Map<String, dynamic> json) =>
    RecipeSummaryOut(
      id: json['id'] as String,
      incompleteNutrients: (json['incomplete_nutrients'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      name: json['name'] as String,
      servings: json['servings'] as num?,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );

Map<String, dynamic> _$RecipeSummaryOutToJson(RecipeSummaryOut instance) =>
    <String, dynamic>{
      'id': instance.id,
      'incomplete_nutrients': instance.incompleteNutrients,
      'name': instance.name,
      'servings': instance.servings,
      'updated_at': instance.updatedAt.toIso8601String(),
    };
