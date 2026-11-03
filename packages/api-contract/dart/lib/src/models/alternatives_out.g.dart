// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alternatives_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AlternativesOut _$AlternativesOutFromJson(Map<String, dynamic> json) =>
    AlternativesOut(
      items: (json['items'] as List<dynamic>)
          .map((e) => AlternativeOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      reason: AlternativesOutReason.fromJson(json['reason'] as String),
    );

Map<String, dynamic> _$AlternativesOutToJson(AlternativesOut instance) =>
    <String, dynamic>{
      'items': instance.items,
      'reason': _$AlternativesOutReasonEnumMap[instance.reason]!,
    };

const _$AlternativesOutReasonEnumMap = {
  AlternativesOutReason.ok: 'ok',
  AlternativesOutReason.noCategory: 'no_category',
  AlternativesOutReason.noBetterFound: 'no_better_found',
  AlternativesOutReason.sourceUngraded: 'source_ungraded',
  AlternativesOutReason.sourceProteinUnknown: 'source_protein_unknown',
  AlternativesOutReason.sourceSupplement: 'source_supplement',
  AlternativesOutReason.$unknown: r'$unknown',
};
