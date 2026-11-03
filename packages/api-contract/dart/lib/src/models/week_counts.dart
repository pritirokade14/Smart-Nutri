// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'week_counts.g.dart';

/// Account-wide counts for the weekly share text. Counts only, no health data.
@JsonSerializable()
class WeekCounts {
  const WeekCounts({
    required this.end,
    required this.logged,
    required this.scans,
    required this.start,
  });

  factory WeekCounts.fromJson(Map<String, Object?> json) =>
      _$WeekCountsFromJson(json);

  final DateTime end;

  /// Meal logs in the 7 IST days, all members
  final int logged;

  /// Products checked (analyses) in the 7 IST days
  final int scans;
  final DateTime start;

  Map<String, Object?> toJson() => _$WeekCountsToJson(this);
}
