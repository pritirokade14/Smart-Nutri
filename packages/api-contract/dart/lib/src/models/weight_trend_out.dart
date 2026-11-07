// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'projection_out.dart';
import 'trend_point_out.dart';
import 'weekly_rate_out.dart';
import 'weight_point_out.dart';
import 'weight_trend_out_days.dart';
import 'weight_trend_out_projection_reason.dart';

part 'weight_trend_out.g.dart';

@JsonSerializable()
class WeightTrendOut {
  const WeightTrendOut({
    required this.days,
    required this.flags,
    required this.from,
    required this.memberId,
    required this.numbersHidden,
    required this.points,
    required this.projection,
    required this.projectionReason,
    required this.to,
    required this.trend,
    required this.weeklyRate,
    this.pendingClinicianReview = true,
  });

  factory WeightTrendOut.fromJson(Map<String, Object?> json) =>
      _$WeightTrendOutFromJson(json);

  final WeightTrendOutDays days;
  final List<String> flags;
  final DateTime from;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'numbers_hidden')
  final bool numbersHidden;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;
  final List<WeightPointOut> points;
  final ProjectionOut? projection;
  @JsonKey(name: 'projection_reason')
  final WeightTrendOutProjectionReason projectionReason;
  final DateTime to;
  final List<TrendPointOut> trend;
  @JsonKey(name: 'weekly_rate')
  final WeeklyRateOut? weeklyRate;

  Map<String, Object?> toJson() => _$WeightTrendOutToJson(this);
}
