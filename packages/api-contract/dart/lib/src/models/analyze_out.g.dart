// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analyze_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnalyzeOut _$AnalyzeOutFromJson(Map<String, dynamic> json) => AnalyzeOut(
  product: ProductOut.fromJson(json['product'] as Map<String, dynamic>),
  report: json['report'],
  scanId: json['scan_id'] as String,
  verdicts: (json['verdicts'] as List<dynamic>)
      .map((e) => VerdictOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  tips:
      (json['tips'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  explanation: json['explanation'] as String?,
);

Map<String, dynamic> _$AnalyzeOutToJson(AnalyzeOut instance) =>
    <String, dynamic>{
      'explanation': instance.explanation,
      'product': instance.product,
      'report': instance.report,
      'scan_id': instance.scanId,
      'tips': instance.tips,
      'verdicts': instance.verdicts,
    };
