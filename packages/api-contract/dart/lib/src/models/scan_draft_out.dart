// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'product_draft.dart';

part 'scan_draft_out.g.dart';

@JsonSerializable()
class ScanDraftOut {
  const ScanDraftOut({
    required this.cached,
    required this.draft,
    required this.promptVersion,
    required this.scanId,
  });

  factory ScanDraftOut.fromJson(Map<String, Object?> json) =>
      _$ScanDraftOutFromJson(json);

  final bool cached;
  final ProductDraft draft;
  @JsonKey(name: 'prompt_version')
  final String promptVersion;
  @JsonKey(name: 'scan_id')
  final String scanId;

  Map<String, Object?> toJson() => _$ScanDraftOutToJson(this);
}
