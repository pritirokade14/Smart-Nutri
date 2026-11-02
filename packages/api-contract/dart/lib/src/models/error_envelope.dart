// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'error_body.dart';

part 'error_envelope.g.dart';

/// The only error shape the API returns (never FastAPI's `{"detail": [...]}`).
@JsonSerializable()
class ErrorEnvelope {
  const ErrorEnvelope({required this.error});

  factory ErrorEnvelope.fromJson(Map<String, Object?> json) =>
      _$ErrorEnvelopeFromJson(json);

  final ErrorBody error;

  Map<String, Object?> toJson() => _$ErrorEnvelopeToJson(this);
}
