// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'day_summary.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DaySummary _$DaySummaryFromJson(Map<String, dynamic> json) => DaySummary(
  bands: NutrientBands.fromJson(json['bands'] as Map<String, dynamic>),
  date: DateTime.parse(json['date'] as String),
  incomplete: IncompleteNutrients.fromJson(
    json['incomplete'] as Map<String, dynamic>,
  ),
  items: (json['items'] as num).toInt(),
  totals: Totals.fromJson(json['totals'] as Map<String, dynamic>),
);

Map<String, dynamic> _$DaySummaryToJson(DaySummary instance) =>
    <String, dynamic>{
      'bands': instance.bands,
      'date': instance.date.toIso8601String(),
      'incomplete': instance.incomplete,
      'items': instance.items,
      'totals': instance.totals,
    };
