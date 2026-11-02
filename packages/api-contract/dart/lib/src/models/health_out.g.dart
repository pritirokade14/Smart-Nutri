// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'health_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HealthOut _$HealthOutFromJson(Map<String, dynamic> json) => HealthOut(
  database: HealthOutDatabase.fromJson(json['database'] as String),
  status: HealthOutStatus.fromJson(json['status'] as String),
);

Map<String, dynamic> _$HealthOutToJson(HealthOut instance) => <String, dynamic>{
  'database': _$HealthOutDatabaseEnumMap[instance.database]!,
  'status': _$HealthOutStatusEnumMap[instance.status]!,
};

const _$HealthOutDatabaseEnumMap = {
  HealthOutDatabase.ok: 'ok',
  HealthOutDatabase.error: 'error',
  HealthOutDatabase.schemaBehind: 'schema_behind',
  HealthOutDatabase.$unknown: r'$unknown',
};

const _$HealthOutStatusEnumMap = {
  HealthOutStatus.ok: 'ok',
  HealthOutStatus.degraded: 'degraded',
  HealthOutStatus.unavailable: 'unavailable',
  HealthOutStatus.$unknown: r'$unknown',
};
