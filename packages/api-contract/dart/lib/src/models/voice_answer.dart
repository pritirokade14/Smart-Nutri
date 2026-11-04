// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'voice_answer_source.dart';
import 'voice_answer_verdict_status.dart';

part 'voice_answer.g.dart';

/// A spoken answer. `answer` always starts with the engine's verdict sentence for.
/// `verdict_status`; clients show it with the "not medical advice" disclaimer and never.
/// derive a verdict from the text.
@JsonSerializable()
class VoiceAnswer {
  const VoiceAnswer({
    required this.answer,
    required this.audioBase64,
    required this.question,
    required this.source,
    required this.verdictStatus,
    this.audioMime = 'audio/mpeg',
  });

  factory VoiceAnswer.fromJson(Map<String, Object?> json) =>
      _$VoiceAnswerFromJson(json);

  /// Engine verdict sentence, then the explanation.
  final String answer;

  /// The spoken answer, base64-encoded (`audio_mime`), sent only in this response and never stored. null when the audio would be over about 1 MB: show `answer` as text.
  @JsonKey(name: 'audio_base64')
  final String? audioBase64;

  /// Media type of audio_base64 (mp3).
  @JsonKey(name: 'audio_mime')
  final String audioMime;

  /// The transcribed question (never stored or logged).
  final String question;

  /// llm: AI explanation that passed every check; fallback: rule-based text.
  final VoiceAnswerSource source;
  @JsonKey(name: 'verdict_status')
  final VoiceAnswerVerdictStatus verdictStatus;

  Map<String, Object?> toJson() => _$VoiceAnswerToJson(this);
}
