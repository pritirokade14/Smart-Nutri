// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'explanation_out.dart';
import 'product_out.dart';
import 'verdict_out.dart';

part 'analyze_out.g.dart';

@JsonSerializable()
class AnalyzeOut {
  const AnalyzeOut({
    required this.explanation,
    required this.product,
    required this.report,
    required this.scanId,
    required this.verdicts,
  });

  factory AnalyzeOut.fromJson(Map<String, Object?> json) =>
      _$AnalyzeOutFromJson(json);

  final ExplanationOut explanation;
  final ProductOut product;
  final dynamic report;
  @JsonKey(name: 'scan_id')
  final String scanId;
  final List<VerdictOut> verdicts;

  Map<String, Object?> toJson() => _$AnalyzeOutToJson(this);
}
