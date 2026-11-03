// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'alternative_out.dart';
import 'alternatives_out_reason.dart';

part 'alternatives_out.g.dart';

@JsonSerializable()
class AlternativesOut {
  const AlternativesOut({required this.items, required this.reason});

  factory AlternativesOut.fromJson(Map<String, Object?> json) =>
      _$AlternativesOutFromJson(json);

  /// At most 5: best grade first, then less sugar, then name
  final List<AlternativeOut> items;
  final AlternativesOutReason reason;

  Map<String, Object?> toJson() => _$AlternativesOutToJson(this);
}
