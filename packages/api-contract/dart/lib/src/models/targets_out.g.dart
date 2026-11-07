// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'targets_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TargetsOut _$TargetsOutFromJson(Map<String, dynamic> json) => TargetsOut(
  basis: json['basis'] == null
      ? null
      : TargetsOutBasis.fromJson(json['basis'] as String),
  carbsG: (json['carbs_g'] as num?)?.toInt(),
  date: DateTime.parse(json['date'] as String),
  direction: json['direction'] == null
      ? null
      : TargetsOutDirection.fromJson(json['direction'] as String),
  energyKcal: (json['energy_kcal'] as num?)?.toInt(),
  explanation: json['explanation'] == null
      ? null
      : TargetsExplanation.fromJson(
          json['explanation'] as Map<String, dynamic>,
        ),
  fatG: (json['fat_g'] as num?)?.toInt(),
  flags: (json['flags'] as List<dynamic>).map((e) => e as String).toList(),
  memberId: json['member_id'] as String,
  missingFields: (json['missing_fields'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  numbersHidden: NumbersHidden.fromJson(
    json['numbers_hidden'] as Map<String, dynamic>,
  ),
  proteinG: (json['protein_g'] as num?)?.toInt(),
  rate: json['rate'] == null
      ? null
      : RateOut.fromJson(json['rate'] as Map<String, dynamic>),
  rateOptions: (json['rate_options'] as List<dynamic>)
      .map((e) => RateOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  sources: (json['sources'] as List<dynamic>).map((e) => e as String).toList(),
  status: TargetsOutStatus.fromJson(json['status'] as String),
  unusualFields: (json['unusual_fields'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  pendingClinicianReview: json['pending_clinician_review'] as bool? ?? true,
);

Map<String, dynamic> _$TargetsOutToJson(TargetsOut instance) =>
    <String, dynamic>{
      'basis': _$TargetsOutBasisEnumMap[instance.basis],
      'carbs_g': instance.carbsG,
      'date': instance.date.toIso8601String(),
      'direction': _$TargetsOutDirectionEnumMap[instance.direction],
      'energy_kcal': instance.energyKcal,
      'explanation': instance.explanation,
      'fat_g': instance.fatG,
      'flags': instance.flags,
      'member_id': instance.memberId,
      'missing_fields': instance.missingFields,
      'numbers_hidden': instance.numbersHidden,
      'pending_clinician_review': instance.pendingClinicianReview,
      'protein_g': instance.proteinG,
      'rate': instance.rate,
      'rate_options': instance.rateOptions,
      'sources': instance.sources,
      'status': _$TargetsOutStatusEnumMap[instance.status]!,
      'unusual_fields': instance.unusualFields,
    };

const _$TargetsOutBasisEnumMap = {
  TargetsOutBasis.formula: 'formula',
  TargetsOutBasis.adaptive: 'adaptive',
  TargetsOutBasis.$unknown: r'$unknown',
};

const _$TargetsOutDirectionEnumMap = {
  TargetsOutDirection.lose: 'lose',
  TargetsOutDirection.maintain: 'maintain',
  TargetsOutDirection.gain: 'gain',
  TargetsOutDirection.$unknown: r'$unknown',
};

const _$TargetsOutStatusEnumMap = {
  TargetsOutStatus.ready: 'ready',
  TargetsOutStatus.needsBodyData: 'needs_body_data',
  TargetsOutStatus.notAvailableMinor: 'not_available_minor',
  TargetsOutStatus.pausedPregnancy: 'paused_pregnancy',
  TargetsOutStatus.none: 'none',
  TargetsOutStatus.$unknown: r'$unknown',
};
