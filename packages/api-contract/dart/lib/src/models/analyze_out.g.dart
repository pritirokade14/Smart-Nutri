// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analyze_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnalyzeOut _$AnalyzeOutFromJson(Map<String, dynamic> json) => AnalyzeOut(
  explanation: ExplanationOut.fromJson(
    json['explanation'] as Map<String, dynamic>,
  ),
  product: ProductOut.fromJson(json['product'] as Map<String, dynamic>),
  report: json['report'],
  scanId: json['scan_id'] as String,
  verdicts: (json['verdicts'] as List<dynamic>)
      .map((e) => VerdictOut.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$AnalyzeOutToJson(AnalyzeOut instance) =>
    <String, dynamic>{
      'explanation': instance.explanation,
      'product': instance.product,
      'report': instance.report,
      'scan_id': instance.scanId,
      'verdicts': instance.verdicts,
    };
