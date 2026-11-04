// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// llm: AI explanation that passed every check; fallback: rule-based text.
@JsonEnum()
enum VoiceAnswerSource {
  @JsonValue('llm')
  llm('llm'),
  @JsonValue('fallback')
  fallback('fallback'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const VoiceAnswerSource(this.json);

  factory VoiceAnswerSource.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<VoiceAnswerSource> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
