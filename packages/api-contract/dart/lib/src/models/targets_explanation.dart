// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'targets_explanation_protein_basis.dart';
import 'targets_explanation_weight_source.dart';

part 'targets_explanation.g.dart';

/// "How we got this". Kcal values are whole kcal, weights 1 dp (Ruling D12). Numbers are.
/// null when hidden (Ruling D11); `protein_basis` is never hidden.
@JsonSerializable()
class TargetsExplanation {
  const TargetsExplanation({
    required this.activityFactor,
    required this.adjustmentKcal,
    required this.bmrKcal,
    required this.bodyFatPctUsed,
    required this.floorKcal,
    required this.ibwKg,
    required this.maintenanceKcal,
    required this.proteinBasis,
    required this.proteinGPerKg,
    required this.proteinReferenceWeightKg,
    required this.weightKgUsed,
    this.weightSource,
  });

  factory TargetsExplanation.fromJson(Map<String, Object?> json) =>
      _$TargetsExplanationFromJson(json);

  @JsonKey(name: 'activity_factor')
  final num? activityFactor;
  @JsonKey(name: 'adjustment_kcal')
  final int? adjustmentKcal;
  @JsonKey(name: 'bmr_kcal')
  final int? bmrKcal;
  @JsonKey(name: 'body_fat_pct_used')
  final num? bodyFatPctUsed;
  @JsonKey(name: 'floor_kcal')
  final int? floorKcal;
  @JsonKey(name: 'ibw_kg')
  final num? ibwKg;
  @JsonKey(name: 'maintenance_kcal')
  final int? maintenanceKcal;
  @JsonKey(name: 'protein_basis')
  final TargetsExplanationProteinBasis proteinBasis;
  @JsonKey(name: 'protein_g_per_kg')
  final num? proteinGPerKg;
  @JsonKey(name: 'protein_reference_weight_kg')
  final num? proteinReferenceWeightKg;
  @JsonKey(name: 'weight_kg_used')
  final num? weightKgUsed;
  @JsonKey(name: 'weight_source')
  final TargetsExplanationWeightSource? weightSource;

  Map<String, Object?> toJson() => _$TargetsExplanationToJson(this);
}
