// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'scan_draft_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ScanDraftOut _$ScanDraftOutFromJson(Map<String, dynamic> json) => ScanDraftOut(
  cached: json['cached'] as bool,
  draft: ProductDraft.fromJson(json['draft'] as Map<String, dynamic>),
  promptVersion: json['prompt_version'] as String,
  scanId: json['scan_id'] as String,
);

Map<String, dynamic> _$ScanDraftOutToJson(ScanDraftOut instance) =>
    <String, dynamic>{
      'cached': instance.cached,
      'draft': instance.draft,
      'prompt_version': instance.promptVersion,
      'scan_id': instance.scanId,
    };
