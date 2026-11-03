// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'report_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ReportOut _$ReportOutFromJson(Map<String, dynamic> json) => ReportOut(
  createdAt: DateTime.parse(json['created_at'] as String),
  id: json['id'] as String,
  productId: json['product_id'] as String,
  reason: ReportOutReason.fromJson(json['reason'] as String),
  status: ReportOutStatus.fromJson(json['status'] as String),
);

Map<String, dynamic> _$ReportOutToJson(ReportOut instance) => <String, dynamic>{
  'created_at': instance.createdAt.toIso8601String(),
  'id': instance.id,
  'product_id': instance.productId,
  'reason': _$ReportOutReasonEnumMap[instance.reason]!,
  'status': _$ReportOutStatusEnumMap[instance.status]!,
};

const _$ReportOutReasonEnumMap = {
  ReportOutReason.wrongValues: 'wrong_values',
  ReportOutReason.wrongIngredients: 'wrong_ingredients',
  ReportOutReason.wrongProduct: 'wrong_product',
  ReportOutReason.other: 'other',
  ReportOutReason.$unknown: r'$unknown',
};

const _$ReportOutStatusEnumMap = {
  ReportOutStatus.open: 'open',
  ReportOutStatus.resolved: 'resolved',
  ReportOutStatus.$unknown: r'$unknown',
};
