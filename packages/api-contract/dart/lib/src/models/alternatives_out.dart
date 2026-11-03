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

  /// At most 5: best grade first, then less sugar, then name. With member_id, never a product the engine rates avoid for that member, and ok before caution before unknown
  final List<AlternativeOut> items;

  /// no_better_found also when every better product is avoid for member_id
  final AlternativesOutReason reason;

  Map<String, Object?> toJson() => _$AlternativesOutToJson(this);
}
