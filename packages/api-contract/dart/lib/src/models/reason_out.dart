// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'reason_out_severity.dart';

part 'reason_out.g.dart';

@JsonSerializable()
class ReasonOut {
  const ReasonOut({
    required this.code,
    required this.params,
    required this.severity,
  });

  factory ReasonOut.fromJson(Map<String, Object?> json) =>
      _$ReasonOutFromJson(json);

  final String code;
  final dynamic params;
  final ReasonOutSeverity severity;

  Map<String, Object?> toJson() => _$ReasonOutToJson(this);
}
