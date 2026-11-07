// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'projection_out.g.dart';

@JsonSerializable()
class ProjectionOut {
  const ProjectionOut({required this.date, required this.targetKg});

  factory ProjectionOut.fromJson(Map<String, Object?> json) =>
      _$ProjectionOutFromJson(json);

  final DateTime? date;
  @JsonKey(name: 'target_kg')
  final num? targetKg;

  Map<String, Object?> toJson() => _$ProjectionOutToJson(this);
}
