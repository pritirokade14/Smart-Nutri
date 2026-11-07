// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'day_tile.dart';
import 'incomplete_nutrients.dart';
import 'macro4.dart';
import 'numbers_hidden.dart';

part 'diary_week_out.g.dart';

@JsonSerializable()
class DiaryWeekOut {
  const DiaryWeekOut({
    required this.averagedDays,
    required this.averages,
    required this.averagesIncomplete,
    required this.days,
    required this.end,
    required this.memberId,
    required this.numbersHidden,
    required this.proteinMetDays,
    required this.start,
    required this.today,
    this.pendingClinicianReview = true,
  });

  factory DiaryWeekOut.fromJson(Map<String, Object?> json) =>
      _$DiaryWeekOutFromJson(json);

  @JsonKey(name: 'averaged_days')
  final int averagedDays;

  /// Per averaged day, 1 dp. Averaged days are those with items that are not marked partial; null when there are none
  final Macro4 averages;

  /// true for a nutrient unknown on any averaged day: its average is a lower bound
  @JsonKey(name: 'averages_incomplete')
  final IncompleteNutrients averagesIncomplete;

  /// 7 days, oldest first
  final List<DayTile> days;
  final DateTime end;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'numbers_hidden')
  final NumbersHidden numbersHidden;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;

  /// Averaged days whose frozen protein target is ready and was met
  @JsonKey(name: 'protein_met_days')
  final int proteinMetDays;
  final DateTime start;
  final DateTime today;

  Map<String, Object?> toJson() => _$DiaryWeekOutToJson(this);
}
