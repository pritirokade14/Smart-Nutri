// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'macro4.g.dart';

/// Energy and the three macros a daily guide covers. null per field: not available.
@JsonSerializable()
class Macro4 {
  const Macro4({
    required this.carbsG,
    required this.energyKcal,
    required this.fatG,
    required this.proteinG,
  });

  factory Macro4.fromJson(Map<String, Object?> json) => _$Macro4FromJson(json);

  @JsonKey(name: 'carbs_g')
  final num? carbsG;
  @JsonKey(name: 'energy_kcal')
  final num? energyKcal;
  @JsonKey(name: 'fat_g')
  final num? fatG;
  @JsonKey(name: 'protein_g')
  final num? proteinG;

  Map<String, Object?> toJson() => _$Macro4ToJson(this);
}
