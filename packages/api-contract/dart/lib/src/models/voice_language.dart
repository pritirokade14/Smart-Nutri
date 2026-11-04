// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Language of the question and of the spoken answer (a named schema, so the generated.
/// clients get a real enum type for the multipart field).
@JsonEnum()
enum VoiceLanguage {
  @JsonValue('en')
  en('en'),
  @JsonValue('hi')
  hi('hi'),
  @JsonValue('mr')
  mr('mr'),

  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const VoiceLanguage(this.json);

  factory VoiceLanguage.fromJson(String json) =>
      values.firstWhere((e) => e.json == json, orElse: () => $unknown);

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();

  /// Returns all defined enum values excluding the $unknown value.
  static List<VoiceLanguage> get $valuesDefined =>
      values.where((value) => value != $unknown).toList();
}
