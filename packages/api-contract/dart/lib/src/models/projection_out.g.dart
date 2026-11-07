// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'projection_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProjectionOut _$ProjectionOutFromJson(Map<String, dynamic> json) =>
    ProjectionOut(
      date: json['date'] == null
          ? null
          : DateTime.parse(json['date'] as String),
      targetKg: json['target_kg'] as num?,
    );

Map<String, dynamic> _$ProjectionOutToJson(ProjectionOut instance) =>
    <String, dynamic>{
      'date': instance.date?.toIso8601String(),
      'target_kg': instance.targetKg,
    };
