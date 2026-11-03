// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'totals.g.dart';

/// Sums of the KNOWN values only; see ``Summary.incomplete``.
@JsonSerializable()
class Totals {
  const Totals({
    required this.energyKcal,
    required this.proteinG,
    required this.saltG,
    required this.sugarsG,
  });

  factory Totals.fromJson(Map<String, Object?> json) => _$TotalsFromJson(json);

  @JsonKey(name: 'energy_kcal')
  final num energyKcal;
  @JsonKey(name: 'protein_g')
  final num proteinG;
  @JsonKey(name: 'salt_g')
  final num saltG;
  @JsonKey(name: 'sugars_g')
  final num sugarsG;

  Map<String, Object?> toJson() => _$TotalsToJson(this);
}
