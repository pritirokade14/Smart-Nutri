// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'diary_day_status_out.g.dart';

@JsonSerializable()
class DiaryDayStatusOut {
  const DiaryDayStatusOut({required this.date, required this.partialLogged});

  factory DiaryDayStatusOut.fromJson(Map<String, Object?> json) =>
      _$DiaryDayStatusOutFromJson(json);

  final DateTime date;
  @JsonKey(name: 'partial_logged')
  final bool partialLogged;

  Map<String, Object?> toJson() => _$DiaryDayStatusOutToJson(this);
}
