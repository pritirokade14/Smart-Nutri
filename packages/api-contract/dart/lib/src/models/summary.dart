// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'daily_limits_out.dart';
import 'day_summary.dart';
import 'incomplete_nutrients.dart';
import 'nutrient_bands.dart';
import 'summary_period.dart';
import 'totals.dart';

part 'summary.g.dart';

@JsonSerializable()
class Summary {
  const Summary({
    required this.bands,
    required this.days,
    required this.end,
    required this.incomplete,
    required this.limits,
    required this.memberId,
    required this.period,
    required this.proteinLeftG,
    required this.start,
    required this.totals,
    this.pendingClinicianReview = true,
  });

  factory Summary.fromJson(Map<String, Object?> json) =>
      _$SummaryFromJson(json);

  final NutrientBands bands;

  /// 1 for day, 7 for week (oldest first)
  final List<DaySummary> days;
  final DateTime end;
  final IncompleteNutrients incomplete;
  final DailyLimitsOut limits;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;
  final SummaryPeriod period;

  /// period=day only: max(0, limits.protein_target_g - totals.protein_g), 1 dp (the whole target when nothing is logged). Null when there is no target, when protein is incomplete for the day, or for period=week. A guide, not a need.
  @JsonKey(name: 'protein_left_g')
  final num? proteinLeftG;
  final DateTime start;
  final Totals totals;

  Map<String, Object?> toJson() => _$SummaryToJson(this);
}
