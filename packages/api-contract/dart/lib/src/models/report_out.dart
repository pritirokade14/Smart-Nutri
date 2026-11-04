// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'report_out_reason.dart';
import 'report_out_status.dart';

part 'report_out.g.dart';

@JsonSerializable()
class ReportOut {
  const ReportOut({
    required this.createdAt,
    required this.id,
    required this.productId,
    required this.reason,
    required this.status,
  });

  factory ReportOut.fromJson(Map<String, Object?> json) =>
      _$ReportOutFromJson(json);

  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  final String id;
  @JsonKey(name: 'product_id')
  final String productId;
  final ReportOutReason reason;
  final ReportOutStatus status;

  Map<String, Object?> toJson() => _$ReportOutToJson(this);
}
