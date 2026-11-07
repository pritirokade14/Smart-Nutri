// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diary_day_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiaryDayOut _$DiaryDayOutFromJson(Map<String, dynamic> json) => DiaryDayOut(
  date: DateTime.parse(json['date'] as String),
  incomplete: IncompleteNutrients.fromJson(
    json['incomplete'] as Map<String, dynamic>,
  ),
  limitsBands: NutrientBands.fromJson(
    json['limits_bands'] as Map<String, dynamic>,
  ),
  memberId: json['member_id'] as String,
  numbersHidden: NumbersHidden.fromJson(
    json['numbers_hidden'] as Map<String, dynamic>,
  ),
  partialLogged: json['partial_logged'] as bool,
  progress: json['progress'] == null
      ? null
      : Macro4.fromJson(json['progress'] as Map<String, dynamic>),
  remaining: json['remaining'] == null
      ? null
      : Macro4.fromJson(json['remaining'] as Map<String, dynamic>),
  slots: (json['slots'] as List<dynamic>)
      .map((e) => SlotDayOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  targets: json['targets'] == null
      ? null
      : TargetsOut.fromJson(json['targets'] as Map<String, dynamic>),
  targetsStatus: DiaryDayOutTargetsStatus.fromJson(
    json['targets_status'] as String,
  ),
  timezone: json['timezone'] as String,
  today: DateTime.parse(json['today'] as String),
  totals: Totals.fromJson(json['totals'] as Map<String, dynamic>),
  pendingClinicianReview: json['pending_clinician_review'] as bool? ?? true,
);

Map<String, dynamic> _$DiaryDayOutToJson(
  DiaryDayOut instance,
) => <String, dynamic>{
  'date': instance.date.toIso8601String(),
  'incomplete': instance.incomplete,
  'limits_bands': instance.limitsBands,
  'member_id': instance.memberId,
  'numbers_hidden': instance.numbersHidden,
  'partial_logged': instance.partialLogged,
  'pending_clinician_review': instance.pendingClinicianReview,
  'progress': instance.progress,
  'remaining': instance.remaining,
  'slots': instance.slots,
  'targets': instance.targets,
  'targets_status': _$DiaryDayOutTargetsStatusEnumMap[instance.targetsStatus]!,
  'timezone': instance.timezone,
  'today': instance.today.toIso8601String(),
  'totals': instance.totals,
};

const _$DiaryDayOutTargetsStatusEnumMap = {
  DiaryDayOutTargetsStatus.ready: 'ready',
  DiaryDayOutTargetsStatus.none: 'none',
  DiaryDayOutTargetsStatus.needsBodyData: 'needs_body_data',
  DiaryDayOutTargetsStatus.notAvailableMinor: 'not_available_minor',
  DiaryDayOutTargetsStatus.pausedPregnancy: 'paused_pregnancy',
  DiaryDayOutTargetsStatus.consentRequired: 'consent_required',
  DiaryDayOutTargetsStatus.$unknown: r'$unknown',
};
