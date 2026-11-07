// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'day_tile_targets.dart';
import 'incomplete_nutrients.dart';
import 'macro4.dart';
import 'nutrient_bands.dart';
import 'totals.dart';

part 'day_tile.g.dart';

@JsonSerializable()
class DayTile {
  const DayTile({
    required this.bands,
    required this.date,
    required this.incomplete,
    required this.items,
    required this.partialLogged,
    required this.progress,
    required this.targets,
    required this.totals,
  });

  factory DayTile.fromJson(Map<String, Object?> json) =>
      _$DayTileFromJson(json);

  final NutrientBands bands;
  final DateTime date;
  final IncompleteNutrients incomplete;
  final int items;
  @JsonKey(name: 'partial_logged')
  final bool partialLogged;
  final Macro4? progress;

  /// That day's frozen energy and protein targets; null without a ready target
  final DayTileTargets? targets;
  final Totals totals;

  Map<String, Object?> toJson() => _$DayTileToJson(this);
}
