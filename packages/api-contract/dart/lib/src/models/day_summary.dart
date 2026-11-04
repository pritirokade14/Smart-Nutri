// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'incomplete_nutrients.dart';
import 'nutrient_bands.dart';
import 'totals.dart';

part 'day_summary.g.dart';

@JsonSerializable()
class DaySummary {
  const DaySummary({
    required this.bands,
    required this.date,
    required this.incomplete,
    required this.items,
    required this.totals,
  });

  factory DaySummary.fromJson(Map<String, Object?> json) =>
      _$DaySummaryFromJson(json);

  /// That day's totals vs the DAILY limits
  final NutrientBands bands;
  final DateTime date;
  final IncompleteNutrients incomplete;
  final int items;
  final Totals totals;

  Map<String, Object?> toJson() => _$DaySummaryToJson(this);
}
