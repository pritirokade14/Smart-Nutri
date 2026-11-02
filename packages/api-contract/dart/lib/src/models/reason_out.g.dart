// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'reason_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ReasonOut _$ReasonOutFromJson(Map<String, dynamic> json) => ReasonOut(
  code: json['code'] as String,
  params: json['params'],
  severity: ReasonOutSeverity.fromJson(json['severity'] as String),
);

Map<String, dynamic> _$ReasonOutToJson(ReasonOut instance) => <String, dynamic>{
  'code': instance.code,
  'params': instance.params,
  'severity': _$ReasonOutSeverityEnumMap[instance.severity]!,
};

const _$ReasonOutSeverityEnumMap = {
  ReasonOutSeverity.ok: 'ok',
  ReasonOutSeverity.caution: 'caution',
  ReasonOutSeverity.unknown: 'unknown',
  ReasonOutSeverity.avoid: 'avoid',
  ReasonOutSeverity.$unknown: r'$unknown',
};
