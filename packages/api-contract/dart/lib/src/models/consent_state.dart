// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'consent_state.g.dart';

@JsonSerializable()
class ConsentState {
  const ConsentState({
    required this.currentVersion,
    required this.granted,
    required this.purpose,
    required this.version,
  });

  factory ConsentState.fromJson(Map<String, Object?> json) =>
      _$ConsentStateFromJson(json);

  @JsonKey(name: 'current_version')
  final String currentVersion;
  final bool granted;
  final String purpose;
  final String? version;

  Map<String, Object?> toJson() => _$ConsentStateToJson(this);
}
