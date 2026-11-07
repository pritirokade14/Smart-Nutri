// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'quick_in.g.dart';

/// A quick add (Plan 11 Ruling E11): kcal and optional macros the person typed. A blank.
/// stays null (never 0), so the entry is incomplete for it. ``name`` is user text: stored.
/// trimmed, never sent to analytics, logs or prompts.
@JsonSerializable()
class QuickIn {
  const QuickIn({
    this.carbsG,
    this.energyKcal,
    this.fatG,
    this.fibreG,
    this.name,
    this.proteinG,
  });

  factory QuickIn.fromJson(Map<String, Object?> json) =>
      _$QuickInFromJson(json);

  @JsonKey(name: 'carbs_g')
  final num? carbsG;
  @JsonKey(name: 'energy_kcal')
  final num? energyKcal;
  @JsonKey(name: 'fat_g')
  final num? fatG;
  @JsonKey(name: 'fibre_g')
  final num? fibreG;
  final String? name;
  @JsonKey(name: 'protein_g')
  final num? proteinG;

  Map<String, Object?> toJson() => _$QuickInToJson(this);
}
