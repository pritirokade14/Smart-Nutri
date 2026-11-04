// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'voice_answer.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VoiceAnswer _$VoiceAnswerFromJson(Map<String, dynamic> json) => VoiceAnswer(
  answer: json['answer'] as String,
  audioBase64: json['audio_base64'] as String?,
  question: json['question'] as String,
  source: VoiceAnswerSource.fromJson(json['source'] as String),
  verdictStatus: VoiceAnswerVerdictStatus.fromJson(
    json['verdict_status'] as String,
  ),
  audioMime: json['audio_mime'] as String? ?? 'audio/mpeg',
);

Map<String, dynamic> _$VoiceAnswerToJson(
  VoiceAnswer instance,
) => <String, dynamic>{
  'answer': instance.answer,
  'audio_base64': instance.audioBase64,
  'audio_mime': instance.audioMime,
  'question': instance.question,
  'source': _$VoiceAnswerSourceEnumMap[instance.source]!,
  'verdict_status': _$VoiceAnswerVerdictStatusEnumMap[instance.verdictStatus]!,
};

const _$VoiceAnswerSourceEnumMap = {
  VoiceAnswerSource.llm: 'llm',
  VoiceAnswerSource.fallback: 'fallback',
  VoiceAnswerSource.$unknown: r'$unknown',
};

const _$VoiceAnswerVerdictStatusEnumMap = {
  VoiceAnswerVerdictStatus.ok: 'ok',
  VoiceAnswerVerdictStatus.caution: 'caution',
  VoiceAnswerVerdictStatus.unknown: 'unknown',
  VoiceAnswerVerdictStatus.avoid: 'avoid',
  VoiceAnswerVerdictStatus.$unknown: r'$unknown',
};
