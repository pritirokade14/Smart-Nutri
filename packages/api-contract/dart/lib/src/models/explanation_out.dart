// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'explanation_out_language.dart';
import 'explanation_out_source.dart';

part 'explanation_out.g.dart';

/// The AI explanation (F7). It explains the verdicts and never changes them.
///
/// `source == "unavailable"` (text null, no tips): no `ai_processing` consent, or the model.
/// failed, timed out or disagreed with the engine. Clients then hide the explanation.
/// `text` and `tips` refer to people only as `member_1`, `member_2`, ...; clients replace.
/// each token with that member's name (or "you") using `member_refs`.
@JsonSerializable()
class ExplanationOut {
  const ExplanationOut({
    required this.language,
    required this.memberRefs,
    required this.promptVersion,
    required this.source,
    required this.text,
    required this.tips,
  });

  factory ExplanationOut.fromJson(Map<String, Object?> json) =>
      _$ExplanationOutFromJson(json);

  final ExplanationOutLanguage language;

  /// `member_N` token -> member_id (a member in `verdicts`). Empty when unavailable.
  @JsonKey(name: 'member_refs')
  final Map<String, String> memberRefs;
  @JsonKey(name: 'prompt_version')
  final String promptVersion;
  final ExplanationOutSource source;
  final String? text;
  final List<String> tips;

  Map<String, Object?> toJson() => _$ExplanationOutToJson(this);
}
