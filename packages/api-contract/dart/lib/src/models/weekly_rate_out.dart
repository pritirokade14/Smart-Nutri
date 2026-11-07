// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'weekly_rate_out.g.dart';

@JsonSerializable()
class WeeklyRateOut {
  const WeeklyRateOut({required this.kg, required this.pctBw});

  factory WeeklyRateOut.fromJson(Map<String, Object?> json) =>
      _$WeeklyRateOutFromJson(json);

  final num kg;
  @JsonKey(name: 'pct_bw')
  final num pctBw;

  Map<String, Object?> toJson() => _$WeeklyRateOutToJson(this);
}
