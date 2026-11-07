// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'weight_point_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeightPointOut _$WeightPointOutFromJson(Map<String, dynamic> json) =>
    WeightPointOut(
      date: DateTime.parse(json['date'] as String),
      outlier: json['outlier'] as bool,
      weightKg: json['weight_kg'] as num?,
      y: json['y'] as num?,
    );

Map<String, dynamic> _$WeightPointOutToJson(WeightPointOut instance) =>
    <String, dynamic>{
      'date': instance.date.toIso8601String(),
      'outlier': instance.outlier,
      'weight_kg': instance.weightKg,
      'y': instance.y,
    };
