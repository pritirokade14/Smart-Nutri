// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'rate_out.g.dart';

/// Unsigned (`direction` carries the sign), 2 dp (Ruling D12).
@JsonSerializable()
class RateOut {
  const RateOut({required this.kgPerWeek, required this.pctBwPerWeek});

  factory RateOut.fromJson(Map<String, Object?> json) =>
      _$RateOutFromJson(json);

  @JsonKey(name: 'kg_per_week')
  final num kgPerWeek;
  @JsonKey(name: 'pct_bw_per_week')
  final num pctBwPerWeek;

  Map<String, Object?> toJson() => _$RateOutToJson(this);
}
