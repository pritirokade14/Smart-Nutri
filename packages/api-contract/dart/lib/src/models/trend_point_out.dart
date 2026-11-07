// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'trend_point_out.g.dart';

@JsonSerializable()
class TrendPointOut {
  const TrendPointOut({
    required this.date,
    required this.trendKg,
    required this.y,
  });

  factory TrendPointOut.fromJson(Map<String, Object?> json) =>
      _$TrendPointOutFromJson(json);

  final DateTime date;
  @JsonKey(name: 'trend_kg')
  final num? trendKg;
  final num? y;

  Map<String, Object?> toJson() => _$TrendPointOutToJson(this);
}
