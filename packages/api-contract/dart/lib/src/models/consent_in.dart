// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'consent_in_purpose.dart';

part 'consent_in.g.dart';

@JsonSerializable()
class ConsentIn {
  const ConsentIn({
    required this.granted,
    required this.purpose,
    required this.version,
  });

  factory ConsentIn.fromJson(Map<String, Object?> json) =>
      _$ConsentInFromJson(json);

  final bool granted;
  final ConsentInPurpose purpose;
  final String version;

  Map<String, Object?> toJson() => _$ConsentInToJson(this);
}
