// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'me_out_language.dart';

part 'me_out.g.dart';

@JsonSerializable()
class MeOut {
  const MeOut({
    required this.createdAt,
    required this.displayName,
    required this.email,
    required this.id,
    required this.language,
    required this.timezone,
  });

  factory MeOut.fromJson(Map<String, Object?> json) => _$MeOutFromJson(json);

  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'display_name')
  final String? displayName;
  final String? email;
  final String id;
  final MeOutLanguage language;
  final String timezone;

  Map<String, Object?> toJson() => _$MeOutToJson(this);
}
