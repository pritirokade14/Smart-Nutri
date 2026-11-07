// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'day_tile_targets.g.dart';

@JsonSerializable()
class DayTileTargets {
  const DayTileTargets({required this.energyKcal, required this.proteinG});

  factory DayTileTargets.fromJson(Map<String, Object?> json) =>
      _$DayTileTargetsFromJson(json);

  @JsonKey(name: 'energy_kcal')
  final int? energyKcal;
  @JsonKey(name: 'protein_g')
  final int? proteinG;

  Map<String, Object?> toJson() => _$DayTileTargetsToJson(this);
}
