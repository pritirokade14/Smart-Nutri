// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trend_point_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TrendPointOut _$TrendPointOutFromJson(Map<String, dynamic> json) =>
    TrendPointOut(
      date: DateTime.parse(json['date'] as String),
      trendKg: json['trend_kg'] as num?,
      y: json['y'] as num?,
    );

Map<String, dynamic> _$TrendPointOutToJson(TrendPointOut instance) =>
    <String, dynamic>{
      'date': instance.date.toIso8601String(),
      'trend_kg': instance.trendKg,
      'y': instance.y,
    };
