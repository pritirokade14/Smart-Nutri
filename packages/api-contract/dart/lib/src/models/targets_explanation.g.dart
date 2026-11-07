// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'targets_explanation.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TargetsExplanation _$TargetsExplanationFromJson(Map<String, dynamic> json) =>
    TargetsExplanation(
      activityFactor: json['activity_factor'] as num?,
      adjustmentKcal: (json['adjustment_kcal'] as num?)?.toInt(),
      bmrKcal: (json['bmr_kcal'] as num?)?.toInt(),
      bodyFatPctUsed: json['body_fat_pct_used'] as num?,
      floorKcal: (json['floor_kcal'] as num?)?.toInt(),
      ibwKg: json['ibw_kg'] as num?,
      maintenanceKcal: (json['maintenance_kcal'] as num?)?.toInt(),
      proteinBasis: TargetsExplanationProteinBasis.fromJson(
        json['protein_basis'] as String,
      ),
      proteinGPerKg: json['protein_g_per_kg'] as num?,
      proteinReferenceWeightKg: json['protein_reference_weight_kg'] as num?,
      weightKgUsed: json['weight_kg_used'] as num?,
      weightSource: json['weight_source'] == null
          ? null
          : TargetsExplanationWeightSource.fromJson(
              json['weight_source'] as String,
            ),
    );

Map<String, dynamic> _$TargetsExplanationToJson(TargetsExplanation instance) =>
    <String, dynamic>{
      'activity_factor': instance.activityFactor,
      'adjustment_kcal': instance.adjustmentKcal,
      'bmr_kcal': instance.bmrKcal,
      'body_fat_pct_used': instance.bodyFatPctUsed,
      'floor_kcal': instance.floorKcal,
      'ibw_kg': instance.ibwKg,
      'maintenance_kcal': instance.maintenanceKcal,
      'protein_basis':
          _$TargetsExplanationProteinBasisEnumMap[instance.proteinBasis]!,
      'protein_g_per_kg': instance.proteinGPerKg,
      'protein_reference_weight_kg': instance.proteinReferenceWeightKg,
      'weight_kg_used': instance.weightKgUsed,
      'weight_source':
          _$TargetsExplanationWeightSourceEnumMap[instance.weightSource],
    };

const _$TargetsExplanationProteinBasisEnumMap = {
  TargetsExplanationProteinBasis.leanMass: 'lean_mass',
  TargetsExplanationProteinBasis.adjustedWeight: 'adjusted_weight',
  TargetsExplanationProteinBasis.actualWeight: 'actual_weight',
  TargetsExplanationProteinBasis.$unknown: r'$unknown',
};

const _$TargetsExplanationWeightSourceEnumMap = {
  TargetsExplanationWeightSource.trend: 'trend',
  TargetsExplanationWeightSource.latest: 'latest',
  TargetsExplanationWeightSource.$unknown: r'$unknown',
};
