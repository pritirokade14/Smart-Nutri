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
    required this.audioUrl,
    required this.question,
    required this.source,
    required this.verdictStatus,
    this.audioExpiresIn = 3600,
  });

  factory VoiceAnswer.fromJson(Map<String, Object?> json) =>
      _$VoiceAnswerFromJson(json);

  /// Engine verdict sentence, then the explanation.
  final String answer;

  /// Seconds until audio_url expires.
  @JsonKey(name: 'audio_expires_in')
  final int audioExpiresIn;

  /// Signed URL of the mp3 answer; expires.
  @JsonKey(name: 'audio_url')
  final String audioUrl;

  /// The transcribed question (never stored or logged).
  final String question;

  /// llm: AI explanation that passed every check; fallback: rule-based text.
  final VoiceAnswerSource source;
  @JsonKey(name: 'verdict_status')
  final VoiceAnswerVerdictStatus verdictStatus;

  Map<String, Object?> toJson() => _$VoiceAnswerToJson(this);
}
