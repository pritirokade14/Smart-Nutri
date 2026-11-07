// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'day_tile_targets.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DayTileTargets _$DayTileTargetsFromJson(Map<String, dynamic> json) =>
    DayTileTargets(
      energyKcal: (json['energy_kcal'] as num?)?.toInt(),
      proteinG: (json['protein_g'] as num?)?.toInt(),
    );

Map<String, dynamic> _$DayTileTargetsToJson(DayTileTargets instance) =>
    <String, dynamic>{
      'energy_kcal': instance.energyKcal,
      'protein_g': instance.proteinG,
    };
