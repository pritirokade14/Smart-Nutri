// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'error_body.g.dart';

/// A stable `code`; clients localise `message_key` (always `error.<code>`).
@JsonSerializable()
class ErrorBody {
  const ErrorBody({
    required this.code,
    required this.details,
    required this.messageKey,
  });

  factory ErrorBody.fromJson(Map<String, Object?> json) =>
      _$ErrorBodyFromJson(json);

  final String code;
  final dynamic details;
  @JsonKey(name: 'message_key')
  final String messageKey;

  Map<String, Object?> toJson() => _$ErrorBodyToJson(this);
}
