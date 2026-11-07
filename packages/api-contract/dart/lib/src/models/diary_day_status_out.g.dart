// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diary_day_status_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiaryDayStatusOut _$DiaryDayStatusOutFromJson(Map<String, dynamic> json) =>
    DiaryDayStatusOut(
      date: DateTime.parse(json['date'] as String),
      partialLogged: json['partial_logged'] as bool,
    );

Map<String, dynamic> _$DiaryDayStatusOutToJson(DiaryDayStatusOut instance) =>
    <String, dynamic>{
      'date': instance.date.toIso8601String(),
      'partial_logged': instance.partialLogged,
    };
