// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'weight_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeightOut _$WeightOutFromJson(Map<String, dynamic> json) => WeightOut(
  clientId: json['client_id'] as String?,
  date: DateTime.parse(json['date'] as String),
  measuredAt: DateTime.parse(json['measured_at'] as String),
  numbersHidden: json['numbers_hidden'] as bool,
  source: json['source'] as String,
  weightKg: json['weight_kg'] as num?,
);

Map<String, dynamic> _$WeightOutToJson(WeightOut instance) => <String, dynamic>{
  'client_id': instance.clientId,
  'date': instance.date.toIso8601String(),
  'measured_at': instance.measuredAt.toIso8601String(),
  'numbers_hidden': instance.numbersHidden,
  'source': instance.source,
  'weight_kg': instance.weightKg,
};
