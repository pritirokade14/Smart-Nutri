// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'health_out.g.dart';

@JsonSerializable()
class HealthOut {
  const HealthOut({required this.database, required this.status});

  factory HealthOut.fromJson(Map<String, Object?> json) =>
      _$HealthOutFromJson(json);

  final String database;
  final String status;

  Map<String, Object?> toJson() => _$HealthOutToJson(this);
}
