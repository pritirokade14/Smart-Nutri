// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'report_create_reason.dart';

part 'report_create.g.dart';

@JsonSerializable()
class ReportCreate {
  const ReportCreate({required this.reason, this.note});

  factory ReportCreate.fromJson(Map<String, Object?> json) =>
      _$ReportCreateFromJson(json);

  final String? note;
  final ReportCreateReason reason;

  Map<String, Object?> toJson() => _$ReportCreateToJson(this);
}
