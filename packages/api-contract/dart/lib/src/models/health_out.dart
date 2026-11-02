// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'health_out_database.dart';
import 'health_out_status.dart';

part 'health_out.g.dart';

/// `ok`/`ok` (200); `degraded`/`error` when the database is unreachable (503);.
/// `unavailable`/`schema_behind` when its Alembic revision is not this build's head (503).
@JsonSerializable()
class HealthOut {
  const HealthOut({required this.database, required this.status});

  factory HealthOut.fromJson(Map<String, Object?> json) =>
      _$HealthOutFromJson(json);

  final HealthOutDatabase database;
  final HealthOutStatus status;

  Map<String, Object?> toJson() => _$HealthOutToJson(this);
}
