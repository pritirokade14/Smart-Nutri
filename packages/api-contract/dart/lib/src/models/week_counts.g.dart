// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'week_counts.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeekCounts _$WeekCountsFromJson(Map<String, dynamic> json) => WeekCounts(
  end: DateTime.parse(json['end'] as String),
  logged: (json['logged'] as num).toInt(),
  scans: (json['scans'] as num).toInt(),
  start: DateTime.parse(json['start'] as String),
);

Map<String, dynamic> _$WeekCountsToJson(WeekCounts instance) =>
    <String, dynamic>{
      'end': instance.end.toIso8601String(),
      'logged': instance.logged,
      'scans': instance.scans,
      'start': instance.start.toIso8601String(),
    };
