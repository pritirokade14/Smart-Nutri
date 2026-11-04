// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'summary.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Summary _$SummaryFromJson(Map<String, dynamic> json) => Summary(
  bands: NutrientBands.fromJson(json['bands'] as Map<String, dynamic>),
  days: (json['days'] as List<dynamic>)
      .map((e) => DaySummary.fromJson(e as Map<String, dynamic>))
      .toList(),
  end: DateTime.parse(json['end'] as String),
  incomplete: IncompleteNutrients.fromJson(
    json['incomplete'] as Map<String, dynamic>,
  ),
  limits: DailyLimitsOut.fromJson(json['limits'] as Map<String, dynamic>),
  memberId: json['member_id'] as String,
  period: SummaryPeriod.fromJson(json['period'] as String),
  proteinLeftG: json['protein_left_g'] as num?,
  start: DateTime.parse(json['start'] as String),
  totals: Totals.fromJson(json['totals'] as Map<String, dynamic>),
  pendingClinicianReview: json['pending_clinician_review'] as bool? ?? true,
);

Map<String, dynamic> _$SummaryToJson(Summary instance) => <String, dynamic>{
  'bands': instance.bands,
  'days': instance.days,
  'end': instance.end.toIso8601String(),
  'incomplete': instance.incomplete,
  'limits': instance.limits,
  'member_id': instance.memberId,
  'pending_clinician_review': instance.pendingClinicianReview,
  'period': _$SummaryPeriodEnumMap[instance.period]!,
  'protein_left_g': instance.proteinLeftG,
  'start': instance.start.toIso8601String(),
  'totals': instance.totals,
};

const _$SummaryPeriodEnumMap = {
  SummaryPeriod.day: 'day',
  SummaryPeriod.week: 'week',
  SummaryPeriod.$unknown: r'$unknown',
};
