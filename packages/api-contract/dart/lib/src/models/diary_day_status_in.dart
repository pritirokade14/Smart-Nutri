// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'diary_day_status_in.g.dart';

@JsonSerializable()
class DiaryDayStatusIn {
  const DiaryDayStatusIn({required this.partialLogged, this.memberId});

  factory DiaryDayStatusIn.fromJson(Map<String, Object?> json) =>
      _$DiaryDayStatusInFromJson(json);

  @JsonKey(name: 'member_id')
  final String? memberId;
  @JsonKey(name: 'partial_logged')
  final bool partialLogged;

  Map<String, Object?> toJson() => _$DiaryDayStatusInToJson(this);
}
