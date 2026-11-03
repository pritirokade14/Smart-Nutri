// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'report_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ReportCreate _$ReportCreateFromJson(Map<String, dynamic> json) => ReportCreate(
  reason: ReportCreateReason.fromJson(json['reason'] as String),
  note: json['note'] as String?,
);

Map<String, dynamic> _$ReportCreateToJson(ReportCreate instance) =>
    <String, dynamic>{
      'note': instance.note,
      'reason': _$ReportCreateReasonEnumMap[instance.reason]!,
    };

const _$ReportCreateReasonEnumMap = {
  ReportCreateReason.wrongValues: 'wrong_values',
  ReportCreateReason.wrongIngredients: 'wrong_ingredients',
  ReportCreateReason.wrongProduct: 'wrong_product',
  ReportCreateReason.other: 'other',
  ReportCreateReason.$unknown: r'$unknown',
};
