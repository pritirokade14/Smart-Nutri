// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diary_week_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiaryWeekOut _$DiaryWeekOutFromJson(Map<String, dynamic> json) => DiaryWeekOut(
  averagedDays: (json['averaged_days'] as num).toInt(),
  averages: Macro4.fromJson(json['averages'] as Map<String, dynamic>),
  averagesIncomplete: IncompleteNutrients.fromJson(
    json['averages_incomplete'] as Map<String, dynamic>,
  ),
  days: (json['days'] as List<dynamic>)
      .map((e) => DayTile.fromJson(e as Map<String, dynamic>))
      .toList(),
  end: DateTime.parse(json['end'] as String),
  memberId: json['member_id'] as String,
  numbersHidden: NumbersHidden.fromJson(
    json['numbers_hidden'] as Map<String, dynamic>,
  ),
  proteinMetDays: (json['protein_met_days'] as num).toInt(),
  start: DateTime.parse(json['start'] as String),
  today: DateTime.parse(json['today'] as String),
  pendingClinicianReview: json['pending_clinician_review'] as bool? ?? true,
);

Map<String, dynamic> _$DiaryWeekOutToJson(DiaryWeekOut instance) =>
    <String, dynamic>{
      'averaged_days': instance.averagedDays,
      'averages': instance.averages,
      'averages_incomplete': instance.averagesIncomplete,
      'days': instance.days,
      'end': instance.end.toIso8601String(),
      'member_id': instance.memberId,
      'numbers_hidden': instance.numbersHidden,
      'pending_clinician_review': instance.pendingClinicianReview,
      'protein_met_days': instance.proteinMetDays,
      'start': instance.start.toIso8601String(),
      'today': instance.today.toIso8601String(),
    };
