// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'diary_day_out_targets_status.dart';
import 'incomplete_nutrients.dart';
import 'macro4.dart';
import 'numbers_hidden.dart';
import 'nutrient_bands.dart';
import 'slot_day_out.dart';
import 'targets_out.dart';
import 'totals.dart';

part 'diary_day_out.g.dart';

@JsonSerializable()
class DiaryDayOut {
  const DiaryDayOut({
    required this.date,
    required this.incomplete,
    required this.limitsBands,
    required this.memberId,
    required this.numbersHidden,
    required this.partialLogged,
    required this.progress,
    required this.remaining,
    required this.slots,
    required this.targets,
    required this.targetsStatus,
    required this.timezone,
    required this.today,
    required this.totals,
    this.pendingClinicianReview = true,
  });

  factory DiaryDayOut.fromJson(Map<String, Object?> json) =>
      _$DiaryDayOutFromJson(json);

  final DateTime date;
  final IncompleteNutrients incomplete;
  @JsonKey(name: 'limits_bands')
  final NutrientBands limitsBands;
  @JsonKey(name: 'member_id')
  final String memberId;
  @JsonKey(name: 'numbers_hidden')
  final NumbersHidden numbersHidden;
  @JsonKey(name: 'partial_logged')
  final bool partialLogged;
  @JsonKey(name: 'pending_clinician_review')
  final bool pendingClinicianReview;

  /// eaten / target, 2 dp (0 with nothing logged); same null rules as `remaining`. A hidden value is rounded to the nearest 0.25: the ring shape only
  final Macro4? progress;

  /// target - eaten, 1 dp; negative means over. null as a whole unless the day's targets are `ready`. A field is null when that nutrient is incomplete (a total with an unknown value is a lower bound) or hidden. With nothing logged it equals the target
  final Macro4? remaining;

  /// The member's active slots in position order, plus an archived slot only on a day that has entries in it
  final List<SlotDayOut> slots;

  /// That day's frozen targets; null when `targets_status` is consent_required
  final TargetsOut? targets;
  @JsonKey(name: 'targets_status')
  final DiaryDayOutTargetsStatus targetsStatus;
  final String timezone;

  /// The account's local today; clients never work out dates
  final DateTime today;
  final Totals totals;

  Map<String, Object?> toJson() => _$DiaryDayOutToJson(this);
}
