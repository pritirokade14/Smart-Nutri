// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'time_window.g.dart';

@JsonSerializable()
class TimeWindow {
  const TimeWindow({required this.end, required this.start});

  factory TimeWindow.fromJson(Map<String, Object?> json) =>
      _$TimeWindowFromJson(json);

  final String end;
  final String start;

  Map<String, Object?> toJson() => _$TimeWindowToJson(this);
}
