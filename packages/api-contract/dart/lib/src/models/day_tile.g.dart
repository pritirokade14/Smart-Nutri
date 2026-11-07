// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'day_tile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DayTile _$DayTileFromJson(Map<String, dynamic> json) => DayTile(
  bands: NutrientBands.fromJson(json['bands'] as Map<String, dynamic>),
  date: DateTime.parse(json['date'] as String),
  incomplete: IncompleteNutrients.fromJson(
    json['incomplete'] as Map<String, dynamic>,
  ),
  items: (json['items'] as num).toInt(),
  partialLogged: json['partial_logged'] as bool,
  progress: json['progress'] == null
      ? null
      : Macro4.fromJson(json['progress'] as Map<String, dynamic>),
  targets: json['targets'] == null
      ? null
      : DayTileTargets.fromJson(json['targets'] as Map<String, dynamic>),
  totals: Totals.fromJson(json['totals'] as Map<String, dynamic>),
);

Map<String, dynamic> _$DayTileToJson(DayTile instance) => <String, dynamic>{
  'bands': instance.bands,
  'date': instance.date.toIso8601String(),
  'incomplete': instance.incomplete,
  'items': instance.items,
  'partial_logged': instance.partialLogged,
  'progress': instance.progress,
  'targets': instance.targets,
  'totals': instance.totals,
};
