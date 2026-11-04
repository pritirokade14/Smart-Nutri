// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'explanation_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ExplanationOut _$ExplanationOutFromJson(Map<String, dynamic> json) =>
    ExplanationOut(
      language: ExplanationOutLanguage.fromJson(json['language'] as String),
      memberRefs: Map<String, String>.from(json['member_refs'] as Map),
      promptVersion: json['prompt_version'] as String,
      source: ExplanationOutSource.fromJson(json['source'] as String),
      text: json['text'] as String?,
      tips: (json['tips'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$ExplanationOutToJson(ExplanationOut instance) =>
    <String, dynamic>{
      'language': _$ExplanationOutLanguageEnumMap[instance.language]!,
      'member_refs': instance.memberRefs,
      'prompt_version': instance.promptVersion,
      'source': _$ExplanationOutSourceEnumMap[instance.source]!,
      'text': instance.text,
      'tips': instance.tips,
    };

const _$ExplanationOutLanguageEnumMap = {
  ExplanationOutLanguage.en: 'en',
  ExplanationOutLanguage.hi: 'hi',
  ExplanationOutLanguage.mr: 'mr',
  ExplanationOutLanguage.$unknown: r'$unknown',
};

const _$ExplanationOutSourceEnumMap = {
  ExplanationOutSource.llm: 'llm',
  ExplanationOutSource.unavailable: 'unavailable',
  ExplanationOutSource.$unknown: r'$unknown',
};
