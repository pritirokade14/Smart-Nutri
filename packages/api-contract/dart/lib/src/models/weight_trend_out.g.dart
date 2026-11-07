// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'weight_trend_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WeightTrendOut _$WeightTrendOutFromJson(Map<String, dynamic> json) =>
    WeightTrendOut(
      days: WeightTrendOutDays.fromJson((json['days'] as num).toInt()),
      flags: (json['flags'] as List<dynamic>).map((e) => e as String).toList(),
      from: DateTime.parse(json['from'] as String),
      memberId: json['member_id'] as String,
      numbersHidden: json['numbers_hidden'] as bool,
      points: (json['points'] as List<dynamic>)
          .map((e) => WeightPointOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      projection: json['projection'] == null
          ? null
          : ProjectionOut.fromJson(json['projection'] as Map<String, dynamic>),
      projectionReason: WeightTrendOutProjectionReason.fromJson(
        json['projection_reason'] as String,
      ),
      rapidLossPct: json['rapid_loss_pct'] as num,
      to: DateTime.parse(json['to'] as String),
      trend: (json['trend'] as List<dynamic>)
          .map((e) => TrendPointOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      weeklyRate: json['weekly_rate'] == null
          ? null
          : WeeklyRateOut.fromJson(json['weekly_rate'] as Map<String, dynamic>),
      pendingClinicianReview: json['pending_clinician_review'] as bool? ?? true,
    );

Map<String, dynamic> _$WeightTrendOutToJson(WeightTrendOut instance) =>
    <String, dynamic>{
      'days': _$WeightTrendOutDaysEnumMap[instance.days]!,
      'flags': instance.flags,
      'from': instance.from.toIso8601String(),
      'member_id': instance.memberId,
      'numbers_hidden': instance.numbersHidden,
      'pending_clinician_review': instance.pendingClinicianReview,
      'points': instance.points,
      'projection': instance.projection,
      'projection_reason':
          _$WeightTrendOutProjectionReasonEnumMap[instance.projectionReason]!,
      'rapid_loss_pct': instance.rapidLossPct,
      'to': instance.to.toIso8601String(),
      'trend': instance.trend,
      'weekly_rate': instance.weeklyRate,
    };

const _$WeightTrendOutDaysEnumMap = {
  WeightTrendOutDays.value30: 30,
  WeightTrendOutDays.value90: 90,
  WeightTrendOutDays.value365: 365,
  WeightTrendOutDays.$unknown: r'$unknown',
};

const _$WeightTrendOutProjectionReasonEnumMap = {
  WeightTrendOutProjectionReason.ready: 'ready',
  WeightTrendOutProjectionReason.tooFewWeighIns: 'too_few_weigh_ins',
  WeightTrendOutProjectionReason.movingAway: 'moving_away',
  WeightTrendOutProjectionReason.noTarget: 'no_target',
  WeightTrendOutProjectionReason.tooFar: 'too_far',
  WeightTrendOutProjectionReason.reached: 'reached',
  WeightTrendOutProjectionReason.$unknown: r'$unknown',
};
